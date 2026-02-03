"""
Tests for pull request webhook handling.

These tests simulate GitHub pull request webhook payloads.
"""

import pytest
import flafl


endpoint = "/flafl/api/v1.0/events"


@pytest.fixture
def client():
    flafl.app.config["TESTING"] = True
    client = flafl.app.test_client()
    yield client


def make_pr_payload(action="opened", number=1, title="PROJ-123: Test PR", merged=False):
    """Helper to create a valid GitHub PR webhook payload."""
    return {
        "action": action,
        "number": number,
        "pull_request": {
            "number": number,
            "title": title,
            "state": "closed" if action == "closed" else "open",
            "merged": merged,
            "html_url": f"https://github.com/owner/repo/pull/{number}",
            "user": {"login": "testuser"},
            "head": {
                "sha": "abc1234567890123456789012345678901234567",
                "ref": "feature/PROJ-123-new-feature",
            },
            "base": {
                "ref": "main",
                "repo": {
                    "name": "test-repo",
                    "owner": {"login": "test-owner"},
                },
            },
        },
    }


# Tests for opened pull requests
# ------------------------------


def test_pr_opened_with_jira_key(client):
    """Test PR opened event with Jira key in title."""
    payload = make_pr_payload(action="opened", title="PROJ-123: Add new feature")
    rv = client.post(
        endpoint,
        json=payload,
        headers={"X-GitHub-Event": "pull_request"},
    )
    json_data = rv.get_json()
    assert json_data["status"] == "success"
    assert "PROJ-123" in json_data["jira_keys"]
    assert "opened" in json_data["message"].lower()


def test_pr_opened_without_jira_key(client):
    """Test PR opened event without Jira key triggers comment."""
    # Create payload without Jira key in title or branch
    payload = {
        "action": "opened",
        "number": 1,
        "pull_request": {
            "number": 1,
            "title": "Add new feature without ticket",
            "state": "open",
            "merged": False,
            "html_url": "https://github.com/owner/repo/pull/1",
            "user": {"login": "testuser"},
            "head": {
                "sha": "abc1234567890123456789012345678901234567",
                "ref": "feature/add-new-feature",  # No Jira key in branch
            },
            "base": {
                "ref": "main",
                "repo": {
                    "name": "test-repo",
                    "owner": {"login": "test-owner"},
                },
            },
        },
    }
    rv = client.post(
        endpoint,
        json=payload,
        headers={"X-GitHub-Event": "pull_request"},
    )
    json_data = rv.get_json()
    assert json_data["status"] == "success"
    assert json_data["jira_keys"] == []
    assert "No Jira keys found" in str(json_data["results"])


def test_pr_opened_jira_key_in_branch(client):
    """Test PR opened event with Jira key only in branch name."""
    payload = make_pr_payload(action="opened", title="Add new feature")
    # Branch already contains PROJ-123 in head ref
    rv = client.post(
        endpoint,
        json=payload,
        headers={"X-GitHub-Event": "pull_request"},
    )
    json_data = rv.get_json()
    assert json_data["status"] == "success"
    assert "PROJ-123" in json_data["jira_keys"]


def test_pr_reopened(client):
    """Test PR reopened event."""
    payload = make_pr_payload(action="reopened", title="PROJ-456: Reopened PR")
    rv = client.post(
        endpoint,
        json=payload,
        headers={"X-GitHub-Event": "pull_request"},
    )
    json_data = rv.get_json()
    assert json_data["status"] == "success"
    assert "PROJ-456" in json_data["jira_keys"]


def test_pr_missing_pull_request_key(client):
    """Test PR event without pull_request key."""
    rv = client.post(
        endpoint,
        json={"action": "opened"},
        headers={"X-GitHub-Event": "pull_request"},
    )
    json_data = rv.get_json()
    assert "does not contain pull_request key" in json_data["message"]


# Tests for closed/merged pull requests
# -------------------------------------


def test_pr_merged(client):
    """Test PR merged event."""
    payload = make_pr_payload(action="closed", title="PROJ-789: Merged PR", merged=True)
    rv = client.post(
        endpoint,
        json=payload,
        headers={"X-GitHub-Event": "pull_request"},
    )
    json_data = rv.get_json()
    assert json_data["status"] == "success"
    assert json_data["merged"] is True
    assert "PROJ-789" in json_data["jira_keys"]
    assert "merged" in json_data["message"].lower()


def test_pr_closed_not_merged(client):
    """Test PR closed without merge."""
    payload = make_pr_payload(action="closed", title="PROJ-999: Closed PR", merged=False)
    rv = client.post(
        endpoint,
        json=payload,
        headers={"X-GitHub-Event": "pull_request"},
    )
    json_data = rv.get_json()
    assert json_data["status"] == "success"
    assert json_data["merged"] is False
    assert "closed" in json_data["message"].lower()


# Tests for synchronized pull requests
# ------------------------------------


def test_pr_synchronized(client):
    """Test PR synchronized event (new commits pushed)."""
    payload = make_pr_payload(action="synchronize", title="PROJ-111: Updated PR")
    rv = client.post(
        endpoint,
        json=payload,
        headers={"X-GitHub-Event": "pull_request"},
    )
    json_data = rv.get_json()
    assert json_data["status"] == "success"
    assert "synchronized" in json_data["message"].lower()
    assert "head_sha" in json_data


# Tests for pull request reviews
# ------------------------------


def test_pr_review_approved(client):
    """Test PR review approved event."""
    payload = make_pr_payload(action="submitted", title="PROJ-222: Review PR")
    payload["review"] = {
        "state": "approved",
        "user": {"login": "reviewer"},
        "body": "LGTM!",
    }
    rv = client.post(
        endpoint,
        json=payload,
        headers={"X-GitHub-Event": "pull_request_review"},
    )
    json_data = rv.get_json()
    assert json_data["status"] == "success"
    assert json_data["review_state"] == "approved"
    assert json_data["reviewer"] == "reviewer"


def test_pr_review_changes_requested(client):
    """Test PR review with changes requested."""
    payload = make_pr_payload(action="submitted", title="PROJ-333: Needs work")
    payload["review"] = {
        "state": "changes_requested",
        "user": {"login": "reviewer"},
        "body": "Please fix the tests.",
    }
    rv = client.post(
        endpoint,
        json=payload,
        headers={"X-GitHub-Event": "pull_request_review"},
    )
    json_data = rv.get_json()
    assert json_data["status"] == "success"
    assert json_data["review_state"] == "changes_requested"


# Tests for issue comments (PR comments)
# --------------------------------------


def test_pr_comment(client):
    """Test comment on PR."""
    payload = {
        "action": "created",
        "issue": {
            "number": 1,
            "title": "PROJ-444: PR with comment",
            "pull_request": {},  # Indicates this is a PR, not an issue
        },
        "comment": {
            "body": "This is a comment",
            "user": {"login": "commenter"},
        },
    }
    rv = client.post(
        endpoint,
        json=payload,
        headers={"X-GitHub-Event": "issue_comment"},
    )
    json_data = rv.get_json()
    assert json_data["status"] == "success"
    assert json_data["commenter"] == "commenter"
    assert "PROJ-444" in json_data["jira_keys"]


# Tests for unhandled PR actions
# ------------------------------


def test_pr_edited(client):
    """Test PR edited action (currently unhandled)."""
    payload = make_pr_payload(action="edited", title="PROJ-555: Edited PR")
    rv = client.post(
        endpoint,
        json=payload,
        headers={"X-GitHub-Event": "pull_request"},
    )
    json_data = rv.get_json()
    assert json_data["status"] == "success"
    assert "unhandled" in json_data["message"].lower()
