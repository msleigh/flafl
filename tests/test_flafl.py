"""
Tests for the main program.

These tests simulate how the program behaves with GitHub webhook payloads.
"""

import pytest
import flafl


endpoint = "/flafl/api/v1.0/events"


@pytest.fixture
def client():
    flafl.app.config["TESTING"] = True
    client = flafl.app.test_client()
    yield client


def test_ping_event(client):
    """Test GitHub ping event (webhook setup verification)."""
    rv = client.post(
        endpoint,
        json={"zen": "Keep it simple.", "hook_id": 12345},
        headers={"X-GitHub-Event": "ping"},
    )
    json_data = rv.get_json()
    assert json_data["status"] == "success"
    assert "Pong!" in json_data["message"]
    assert json_data["hook_id"] == 12345


def test_missing_github_event_header(client):
    """Test request without X-GitHub-Event header."""
    rv = client.post(endpoint, json={"action": "opened"})
    json_data = rv.get_json()
    assert "Missing X-GitHub-Event header" in json_data["message"]


def test_health_check(client):
    """Test health check endpoint."""
    rv = client.get("/flafl/api/v1.0/health")
    json_data = rv.get_json()
    assert json_data["status"] == "healthy"


def test_unhandled_event(client):
    """Test unhandled event type."""
    rv = client.post(
        endpoint,
        json={"action": "created"},
        headers={"X-GitHub-Event": "unknown_event"},
    )
    json_data = rv.get_json()
    assert json_data["status"] == "success"
    assert "unhandled event" in json_data["message"].lower()


class TestJiraKeyExtraction:
    """Tests for Jira key extraction from text."""

    def test_extract_single_key(self):
        from flafl.jsonparser import extract_jira_keys

        keys = extract_jira_keys("PROJ-123: Add new feature")
        assert keys == ["PROJ-123"]

    def test_extract_multiple_keys(self):
        from flafl.jsonparser import extract_jira_keys

        keys = extract_jira_keys("PROJ-123, ABC-456: Fix bugs")
        assert set(keys) == {"PROJ-123", "ABC-456"}

    def test_extract_no_keys(self):
        from flafl.jsonparser import extract_jira_keys

        keys = extract_jira_keys("Add new feature without ticket")
        assert keys == []

    def test_extract_from_branch_name(self):
        from flafl.jsonparser import extract_jira_keys

        keys = extract_jira_keys("feature/PROJ-789-add-login")
        assert keys == ["PROJ-789"]

    def test_extract_empty_string(self):
        from flafl.jsonparser import extract_jira_keys

        keys = extract_jira_keys("")
        assert keys == []

    def test_extract_none(self):
        from flafl.jsonparser import extract_jira_keys

        keys = extract_jira_keys(None)
        assert keys == []
