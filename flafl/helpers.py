"""Helper functions for GitHub/Jira integration."""

import datetime


def log(log_entry):
    """Write a log entry to the log file."""
    with open(__package__ + ".log", "a") as file_pointer:
        file_pointer.write(str(datetime.datetime.now()) + "\n")
        file_pointer.write(log_entry)
        file_pointer.write("\n")


def add_missing_jira_comment(conns, pr_info):
    """
    Add a comment to the PR asking for a Jira ticket reference.

    Args:
        conns: Dict of connections (github, jira)
        pr_info: Dict with PR information (repo_owner, repo_name, number, title)
    """
    github_conn = conns.get("github")
    if not github_conn:
        log("ERROR: No GitHub connection - cannot add comment")
        return

    comment = (
        "This pull request doesn't appear to reference a Jira ticket. "
        "Please include the Jira issue key in the PR title or description "
        "(e.g., `PROJ-123: Add new feature`).\n\n"
        "This helps us automatically track progress in Jira."
    )

    try:
        response = github_conn.add_pr_comment(
            pr_info["repo_owner"],
            pr_info["repo_name"],
            pr_info["number"],
            comment,
        )
        if response.status_code == 201:
            log(f"Added missing Jira comment to PR #{pr_info['number']}")
        else:
            log(f"Failed to add comment: {response.status_code} - {response.text}")
    except Exception as e:
        log(f"ERROR adding comment to PR: {e}")


def transition_jira_issue(conns, issue_key, target_status, pr_info):
    """
    Transition a Jira issue to a target status and add a comment.

    Args:
        conns: Dict of connections (github, jira)
        issue_key: Jira issue key (e.g., PROJ-123)
        target_status: Target status name (e.g., "In Review", "Done")
        pr_info: Dict with PR information

    Returns:
        Tuple of (success: bool, message: str)
    """
    jira_conn = conns.get("jira")
    if not jira_conn:
        msg = f"No Jira connection - cannot transition {issue_key}"
        log(f"ERROR: {msg}")
        return False, msg

    # First, add a comment about the PR
    pr_url = pr_info.get("html_url", "")
    pr_number = pr_info.get("number", "")
    pr_title = pr_info.get("title", "")

    comment = (
        f"PR #{pr_number} ({pr_title}) - transitioning to {target_status}\n{pr_url}"
    )

    try:
        jira_conn.add_comment(issue_key, comment)
    except Exception as e:
        log(f"Warning: Could not add comment to {issue_key}: {e}")

    # Then transition the issue
    try:
        success, msg = jira_conn.transition_to_status(issue_key, target_status)
        log(f"Jira transition for {issue_key}: {msg}")
        return success, msg
    except Exception as e:
        msg = f"Failed to transition {issue_key}: {e}"
        log(f"ERROR: {msg}")
        return False, msg


def add_jira_comment(conns, issue_key, comment_text):
    """
    Add a comment to a Jira issue.

    Args:
        conns: Dict of connections
        issue_key: Jira issue key
        comment_text: Comment text to add

    Returns:
        Tuple of (success: bool, message: str)
    """
    jira_conn = conns.get("jira")
    if not jira_conn:
        msg = f"No Jira connection - cannot add comment to {issue_key}"
        log(f"ERROR: {msg}")
        return False, msg

    try:
        response = jira_conn.add_comment(issue_key, comment_text)
        if response.status_code == 201:
            msg = f"Added comment to {issue_key}"
            log(msg)
            return True, msg
        else:
            msg = f"Failed to add comment to {issue_key}: {response.status_code}"
            log(f"ERROR: {msg}")
            return False, msg
    except Exception as e:
        msg = f"Failed to add comment to {issue_key}: {e}"
        log(f"ERROR: {msg}")
        return False, msg
