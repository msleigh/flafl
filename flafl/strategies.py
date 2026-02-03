"""
Strategies for handling GitHub webhook events and updating Jira.

Each strategy handles a specific type of GitHub event and performs
the appropriate Jira transitions.
"""

import abc
from flask import jsonify

from . import exceptions
from . import helpers
from . import jsonparser

INVALID_USAGE = exceptions.InvalidUsage


class Strategy:
    """
    Declare an interface common to all supported algorithms. Context
    uses this interface to call the algorithm defined by a
    concrete strategy.
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def execute(self, json_data, debug_info, conns, config):
        pass


class PrOpened(Strategy):
    """Strategy for when a pull request is opened."""

    def execute(self, json_data, debug_info, conns, config):
        pr_info = jsonparser.get_pr_info(json_data, debug_info)
        jira_keys = jsonparser.extract_jira_keys_from_pr(json_data, debug_info)

        results = []

        # Check if PR has Jira ticket reference
        if not jira_keys:
            # Add comment to PR asking for Jira ticket
            helpers.add_missing_jira_comment(conns, pr_info)
            results.append("No Jira keys found in PR - comment added")
        else:
            # Transition each Jira ticket to "In Review" (or configured status)
            target_status = config.get("status_on_pr_opened", "In Review")
            for key in jira_keys:
                success, msg = helpers.transition_jira_issue(
                    conns, key, target_status, pr_info
                )
                results.append(msg)

        message = f"PR #{pr_info['number']} opened: {pr_info['title']}"
        return jsonify({
            "status": "success",
            "message": message,
            "jira_keys": jira_keys,
            "results": results,
        })


class PrClosed(Strategy):
    """Strategy for when a pull request is closed (merged or declined)."""

    def execute(self, json_data, debug_info, conns, config):
        pr_info = jsonparser.get_pr_info(json_data, debug_info)
        jira_keys = jsonparser.extract_jira_keys_from_pr(json_data, debug_info)
        was_merged = jsonparser.is_pr_merged(json_data)

        results = []

        if jira_keys:
            if was_merged:
                # PR was merged - transition to "Done" or configured status
                target_status = config.get("status_on_pr_merged", "Done")
                for key in jira_keys:
                    success, msg = helpers.transition_jira_issue(
                        conns, key, target_status, pr_info
                    )
                    results.append(msg)
                action = "merged"
            else:
                # PR was closed without merge - optionally transition back
                target_status = config.get("status_on_pr_declined")
                if target_status:
                    for key in jira_keys:
                        success, msg = helpers.transition_jira_issue(
                            conns, key, target_status, pr_info
                        )
                        results.append(msg)
                action = "closed without merge"
        else:
            action = "merged" if was_merged else "closed"
            results.append("No Jira keys found in PR")

        message = f"PR #{pr_info['number']} {action}: {pr_info['title']}"
        return jsonify({
            "status": "success",
            "message": message,
            "jira_keys": jira_keys,
            "merged": was_merged,
            "results": results,
        })


class PrSynchronize(Strategy):
    """Strategy for when a pull request is updated with new commits."""

    def execute(self, json_data, debug_info, conns, config):
        pr_info = jsonparser.get_pr_info(json_data, debug_info)
        jira_keys = jsonparser.extract_jira_keys_from_pr(json_data, debug_info)

        # Optionally add a comment to Jira about the new commits
        results = []
        if jira_keys and config.get("comment_on_pr_sync", False):
            for key in jira_keys:
                success, msg = helpers.add_jira_comment(
                    conns,
                    key,
                    f"PR #{pr_info['number']} updated with new commits. "
                    f"Latest: {pr_info['head_sha'][:7]}"
                )
                results.append(msg)

        message = f"PR #{pr_info['number']} synchronized: {pr_info['head_sha'][:7]}"
        return jsonify({
            "status": "success",
            "message": message,
            "jira_keys": jira_keys,
            "head_sha": pr_info["head_sha"],
            "results": results,
        })


class PrReviewSubmitted(Strategy):
    """Strategy for when a pull request review is submitted."""

    def execute(self, json_data, debug_info, conns, config):
        pr_info = jsonparser.get_pr_info(json_data, debug_info)
        review_info = jsonparser.get_review_info(json_data, debug_info)
        jira_keys = jsonparser.extract_jira_keys_from_pr(json_data, debug_info)

        results = []
        review_state = review_info["state"]

        if jira_keys:
            if review_state == "approved":
                # Review approved - optionally transition to "Approved" or similar
                target_status = config.get("status_on_review_approved")
                if target_status:
                    for key in jira_keys:
                        success, msg = helpers.transition_jira_issue(
                            conns, key, target_status, pr_info
                        )
                        results.append(msg)

            elif review_state == "changes_requested":
                # Changes requested - optionally transition back to "In Progress"
                target_status = config.get("status_on_changes_requested")
                if target_status:
                    for key in jira_keys:
                        success, msg = helpers.transition_jira_issue(
                            conns, key, target_status, pr_info
                        )
                        results.append(msg)

        message = f"PR #{pr_info['number']} review {review_state} by {review_info['user']}"
        return jsonify({
            "status": "success",
            "message": message,
            "jira_keys": jira_keys,
            "review_state": review_state,
            "reviewer": review_info["user"],
            "results": results,
        })


class PrComment(Strategy):
    """Strategy for comments on pull requests."""

    def execute(self, json_data, debug_info, conns, config):
        # For issue_comment events, PR info is in 'issue' not 'pull_request'
        issue = json_data.get("issue", {})
        comment_info = jsonparser.get_comment_info(json_data, debug_info)

        pr_number = issue.get("number")
        pr_title = issue.get("title", "")

        # Extract Jira keys from the issue/PR title
        jira_keys = jsonparser.extract_jira_keys(pr_title)

        message = f"Comment on PR #{pr_number} by {comment_info['user']}"
        return jsonify({
            "status": "success",
            "message": message,
            "jira_keys": jira_keys,
            "commenter": comment_info["user"],
        })


class Push(Strategy):
    """Strategy for push events (direct pushes to branches)."""

    def execute(self, json_data, debug_info, conns, config):
        ref = json_data.get("ref", "")
        commits = json_data.get("commits", [])
        repo = json_data.get("repository", {})

        # Extract Jira keys from commit messages
        jira_keys = set()
        for commit in commits:
            commit_msg = commit.get("message", "")
            jira_keys.update(jsonparser.extract_jira_keys(commit_msg))

        jira_keys = list(jira_keys)

        message = f"Push to {ref} with {len(commits)} commits"
        return jsonify({
            "status": "success",
            "message": message,
            "jira_keys": jira_keys,
            "ref": ref,
            "commit_count": len(commits),
        })


class Ping(Strategy):
    """Strategy for GitHub ping events (webhook setup verification)."""

    def execute(self, json_data, debug_info, conns, config):
        zen = json_data.get("zen", "")
        hook_id = json_data.get("hook_id")

        message = f"Pong! Webhook {hook_id} connected successfully."
        return jsonify({
            "status": "success",
            "message": message,
            "zen": zen,
            "hook_id": hook_id,
        })


class Unhandled(Strategy):
    """Strategy for unhandled event types."""

    def execute(self, json_data, debug_info, conns, config):
        event_type = debug_info.get("event_type", "unknown")
        action = debug_info.get("action", "unknown")

        message = f"Received unhandled event: {event_type}/{action}"
        return jsonify({
            "status": "success",
            "message": message,
            "event_type": event_type,
            "action": action,
        })
