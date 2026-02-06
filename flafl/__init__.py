"""
FLAFL - Flask Application For Listening (to GitHub webhooks)

Listens for GitHub webhook events and updates Jira tickets accordingly.
Supports PR lifecycle events: opened, closed/merged, synchronized, reviewed.
"""

import json
import os

from flask import Flask, jsonify, request

from . import context
from . import exceptions
from . import github
from . import helpers
from . import jira
from . import jsonparser
from . import strategies


# Configuration from environment variables
def get_env(key, default=None, required=False):
    """Get environment variable with optional default."""
    value = os.environ.get(key, default)
    if required and value is None:
        print(f"ERROR: {key} not specified")
    return value


# Jira configuration
JIRA_BASE_URL = get_env("JIRA_BASE_URL", required=True)
JIRA_USER_EMAIL = get_env("JIRA_USER_EMAIL", required=True)
JIRA_API_TOKEN = get_env("JIRA_API_TOKEN", required=True)

# GitHub configuration (for commenting on PRs)
GITHUB_TOKEN = get_env("GITHUB_TOKEN", required=True)

# Webhook secret for verifying GitHub signatures (optional but recommended)
WEBHOOK_SECRET = get_env("WEBHOOK_SECRET")

# Status transition configuration (customize for your Jira workflow)
CONFIG = {
    # Status to transition to when PR is opened
    "status_on_pr_opened": get_env("STATUS_ON_PR_OPENED", "In Review"),
    # Status to transition to when PR is merged
    "status_on_pr_merged": get_env("STATUS_ON_PR_MERGED", "Done"),
    # Status to transition to when PR is closed without merge (optional)
    "status_on_pr_declined": get_env("STATUS_ON_PR_DECLINED"),
    # Status to transition to when review is approved (optional)
    "status_on_review_approved": get_env("STATUS_ON_REVIEW_APPROVED"),
    # Status to transition to when changes are requested (optional)
    "status_on_changes_requested": get_env("STATUS_ON_CHANGES_REQUESTED"),
    # Whether to add Jira comments when PR is synchronized
    "comment_on_pr_sync": get_env("COMMENT_ON_PR_SYNC", "false").lower() == "true",
}

# Initialize connections
conns = {}

try:
    if JIRA_BASE_URL and JIRA_USER_EMAIL and JIRA_API_TOKEN:
        conns["jira"] = jira.JiraConnection(
            JIRA_BASE_URL, JIRA_USER_EMAIL, JIRA_API_TOKEN
        )
    else:
        conns["jira"] = None
        print("WARNING: Jira connection not configured")
except Exception as e:
    print(f"ERROR: Failed to create Jira connection: {e}")
    conns["jira"] = None

try:
    if GITHUB_TOKEN:
        conns["github"] = github.GitHubConnection(GITHUB_TOKEN)
    else:
        conns["github"] = None
        print("WARNING: GitHub connection not configured")
except Exception as e:
    print(f"ERROR: Failed to create GitHub connection: {e}")
    conns["github"] = None


app = Flask(__name__)


@app.errorhandler(exceptions.InvalidUsage)
def handle_invalid_usage(error):
    """Error handler for InvalidUsage exception."""
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/flafl/api/v1.0/events", methods=["POST"])
def post_event():
    """
    Main webhook endpoint for GitHub events.

    GitHub sends the event type in the X-GitHub-Event header.
    The action (opened, closed, etc.) is in the JSON payload.
    """
    debug_info = {}
    debug_info["payload_received"] = request.json

    # Get the GitHub event type from header
    github_event = request.headers.get("X-GitHub-Event")
    debug_info["github_event"] = github_event

    # Handle ping events (webhook setup verification)
    if github_event == "ping" or jsonparser.is_ping_event(request.json):
        concrete_strategy = strategies.Ping()
        ct = context.Context(concrete_strategy)
        return ct.execute_strategy(request.json, debug_info, conns, CONFIG)

    # Get event type and action
    event_type, action = jsonparser.get_event_type(
        request.json, github_event, debug_info
    )
    debug_info["event_type"] = event_type
    debug_info["action"] = action

    # Route to appropriate strategy based on event type and action
    concrete_strategy = select_strategy(event_type, action)

    # Execute the strategy
    ct = context.Context(concrete_strategy)
    result = ct.execute_strategy(request.json, debug_info, conns, CONFIG)

    # Log the result
    try:
        helpers.log(
            f"Event: {event_type}/{action}\n"
            + json.dumps(result.get_json(), sort_keys=True, indent=2)
        )
    except (TypeError, AttributeError):
        pass

    return result


def select_strategy(event_type, action):
    """
    Select the appropriate strategy based on GitHub event type and action.

    Args:
        event_type: GitHub event type (pull_request, pull_request_review, etc.)
        action: Event action (opened, closed, synchronize, submitted, etc.)

    Returns:
        Strategy instance
    """
    # Pull request events
    if event_type == "pull_request":
        if action == "opened" or action == "reopened":
            return strategies.PrOpened()
        elif action == "closed":
            return strategies.PrClosed()
        elif action == "synchronize":
            return strategies.PrSynchronize()
        # edited, assigned, unassigned, etc. - currently unhandled
        else:
            return strategies.Unhandled()

    # Pull request review events
    elif event_type == "pull_request_review":
        if action == "submitted":
            return strategies.PrReviewSubmitted()
        else:
            return strategies.Unhandled()

    # Issue comment events (includes PR comments)
    elif event_type == "issue_comment":
        if action == "created":
            return strategies.PrComment()
        else:
            return strategies.Unhandled()

    # Push events
    elif event_type == "push":
        return strategies.Push()

    # Unhandled event type
    else:
        return strategies.Unhandled()


@app.route("/flafl/api/v1.0/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify(
        {
            "status": "healthy",
            "jira_connected": conns.get("jira") is not None,
            "github_connected": conns.get("github") is not None,
        }
    )
