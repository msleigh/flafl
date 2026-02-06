"""Helper functions for parsing JSON payloads from GitHub webhooks."""

import re

from . import exceptions

INVALID_USAGE = exceptions.InvalidUsage

# Regex pattern for Jira issue keys (e.g., PROJ-123, ABC-1)
JIRA_KEY_PATTERN = re.compile(r"([A-Z][A-Z0-9]+-\d+)")


def is_ping_event(json_data):
    """Check if event is a GitHub ping (connection test)."""
    return "zen" in json_data and "hook_id" in json_data


def get_event_type(json_data, github_event_header, debug_info):
    """
    Determine the event type from GitHub webhook payload.

    GitHub webhooks use a combination of X-GitHub-Event header and
    the 'action' field in the payload.

    Args:
        json_data: Webhook JSON payload
        github_event_header: Value of X-GitHub-Event header
        debug_info: Debug info dict to populate

    Returns:
        Tuple of (event_type, action)
        event_type: 'pull_request', 'pull_request_review', 'issue_comment', etc.
        action: 'opened', 'closed', 'synchronize', 'submitted', etc.
    """
    if not github_event_header:
        message = "Missing X-GitHub-Event header"
        raise INVALID_USAGE(message, status_code=400, payload=debug_info)

    action = json_data.get("action")
    return github_event_header, action


def get_pr_info(json_data, debug_info):
    """
    Extract pull request information from webhook payload.

    Args:
        json_data: Webhook JSON payload
        debug_info: Debug info dict

    Returns:
        Dict with PR info: number, title, state, merged, head_sha, base_ref, head_ref,
                          repo_owner, repo_name, html_url
    """
    pr = json_data.get("pull_request")
    if not pr:
        message = "Payload does not contain pull_request key"
        raise INVALID_USAGE(message, status_code=400, payload=debug_info)

    try:
        pr_info = {
            "number": pr["number"],
            "title": pr["title"],
            "state": pr["state"],
            "merged": pr.get("merged", False),
            "head_sha": pr["head"]["sha"],
            "head_ref": pr["head"]["ref"],
            "base_ref": pr["base"]["ref"],
            "repo_owner": pr["base"]["repo"]["owner"]["login"],
            "repo_name": pr["base"]["repo"]["name"],
            "html_url": pr["html_url"],
            "user": pr["user"]["login"],
        }
    except KeyError as e:
        message = f"Pull request payload missing required field: {e}"
        raise INVALID_USAGE(message, status_code=400, payload=debug_info)

    return pr_info


def extract_jira_keys(text):
    """
    Extract all Jira issue keys from text.

    Looks for patterns like PROJ-123, ABC-1, etc.

    Args:
        text: String to search for Jira keys

    Returns:
        List of unique Jira issue keys found
    """
    if not text:
        return []
    matches = JIRA_KEY_PATTERN.findall(text)
    return list(set(matches))  # Remove duplicates


def extract_jira_keys_from_pr(json_data, debug_info):
    """
    Extract Jira keys from PR title, branch name, and commit messages.

    Args:
        json_data: Webhook JSON payload
        debug_info: Debug info dict

    Returns:
        List of unique Jira issue keys found
    """
    keys = set()

    pr = json_data.get("pull_request", {})

    # Check PR title
    title = pr.get("title", "")
    keys.update(extract_jira_keys(title))

    # Check head branch name
    head_ref = pr.get("head", {}).get("ref", "")
    keys.update(extract_jira_keys(head_ref))

    # Check PR body/description
    body = pr.get("body", "") or ""
    keys.update(extract_jira_keys(body))

    return list(keys)


def is_pr_merged(json_data):
    """Check if the PR was merged (for closed events)."""
    pr = json_data.get("pull_request", {})
    return pr.get("merged", False)


def get_review_info(json_data, debug_info):
    """
    Extract review information from pull_request_review webhook.

    Args:
        json_data: Webhook JSON payload
        debug_info: Debug info dict

    Returns:
        Dict with review info: state, user, body
    """
    review = json_data.get("review")
    if not review:
        message = "Payload does not contain review key"
        raise INVALID_USAGE(message, status_code=400, payload=debug_info)

    return {
        "state": review.get("state"),  # 'approved', 'changes_requested', 'commented'
        "user": review.get("user", {}).get("login"),
        "body": review.get("body", ""),
    }


def get_comment_info(json_data, debug_info):
    """
    Extract comment information from issue_comment webhook.

    Args:
        json_data: Webhook JSON payload
        debug_info: Debug info dict

    Returns:
        Dict with comment info: body, user
    """
    comment = json_data.get("comment")
    if not comment:
        message = "Payload does not contain comment key"
        raise INVALID_USAGE(message, status_code=400, payload=debug_info)

    return {
        "body": comment.get("body", ""),
        "user": comment.get("user", {}).get("login"),
    }
