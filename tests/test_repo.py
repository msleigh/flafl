"""
Tests for repository webhook handling.

These tests simulate GitHub push event payloads.
"""

import pytest
import flafl


endpoint = "/flafl/api/v1.0/events"


@pytest.fixture
def client():
    flafl.app.config["TESTING"] = True
    client = flafl.app.test_client()
    yield client


def test_push_event_with_jira_keys(client):
    """Test push event extracts Jira keys from commit messages."""
    rv = client.post(
        endpoint,
        json={
            "ref": "refs/heads/main",
            "commits": [
                {"message": "PROJ-123: Add new feature"},
                {"message": "PROJ-456: Fix bug"},
            ],
            "repository": {
                "name": "test-repo",
                "owner": {"login": "test-owner"},
            },
        },
        headers={"X-GitHub-Event": "push"},
    )
    json_data = rv.get_json()
    assert json_data["status"] == "success"
    assert "push" in json_data["message"].lower()
    assert set(json_data["jira_keys"]) == {"PROJ-123", "PROJ-456"}
    assert json_data["commit_count"] == 2


def test_push_event_without_jira_keys(client):
    """Test push event without Jira keys in commits."""
    rv = client.post(
        endpoint,
        json={
            "ref": "refs/heads/feature-branch",
            "commits": [
                {"message": "Add new feature"},
                {"message": "Fix bug"},
            ],
            "repository": {
                "name": "test-repo",
            },
        },
        headers={"X-GitHub-Event": "push"},
    )
    json_data = rv.get_json()
    assert json_data["status"] == "success"
    assert json_data["jira_keys"] == []


def test_push_event_empty_commits(client):
    """Test push event with no commits (e.g., branch deletion)."""
    rv = client.post(
        endpoint,
        json={
            "ref": "refs/heads/deleted-branch",
            "commits": [],
            "repository": {
                "name": "test-repo",
            },
        },
        headers={"X-GitHub-Event": "push"},
    )
    json_data = rv.get_json()
    assert json_data["status"] == "success"
    assert json_data["commit_count"] == 0
