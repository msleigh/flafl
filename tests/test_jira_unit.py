"""Unit tests for flafl.jira."""

from types import SimpleNamespace

from flafl import jira


def test_jira_connection_init_normalizes_url():
    conn = jira.JiraConnection("https://example.atlassian.net/", "u@example.com", "tok")

    assert conn.base_url == "https://example.atlassian.net"
    assert conn.api_url == "https://example.atlassian.net/rest/api/3"
    assert conn.auth == ("u@example.com", "tok")
    assert conn.headers["Accept"] == "application/json"
    assert conn.headers["Content-Type"] == "application/json"


def test_jira_get_issue_calls_requests_get(monkeypatch):
    called = {}
    response = SimpleNamespace(status_code=200)

    def fake_get(url, auth, headers):
        called["url"] = url
        called["auth"] = auth
        called["headers"] = headers
        return response

    monkeypatch.setattr(jira.requests, "get", fake_get)
    conn = jira.JiraConnection("https://example.atlassian.net", "u", "t")

    out = conn.get_issue("PROJ-1")

    assert out is response
    assert called["url"].endswith("/issue/PROJ-1")
    assert called["auth"] == ("u", "t")
    assert called["headers"] == conn.headers


def test_jira_get_transitions_calls_requests_get(monkeypatch):
    called = {}
    response = SimpleNamespace(status_code=200)

    def fake_get(url, auth, headers):
        called["url"] = url
        called["auth"] = auth
        called["headers"] = headers
        return response

    monkeypatch.setattr(jira.requests, "get", fake_get)
    conn = jira.JiraConnection("https://example.atlassian.net", "u", "t")

    out = conn.get_transitions("PROJ-2")

    assert out is response
    assert called["url"].endswith("/issue/PROJ-2/transitions")
    assert called["auth"] == ("u", "t")
    assert called["headers"] == conn.headers


def test_jira_transition_issue_calls_requests_post(monkeypatch):
    called = {}
    response = SimpleNamespace(status_code=204)

    def fake_post(url, auth, headers, json):
        called["url"] = url
        called["auth"] = auth
        called["headers"] = headers
        called["json"] = json
        return response

    monkeypatch.setattr(jira.requests, "post", fake_post)
    conn = jira.JiraConnection("https://example.atlassian.net", "u", "t")

    out = conn.transition_issue("PROJ-3", 55)

    assert out is response
    assert called["url"].endswith("/issue/PROJ-3/transitions")
    assert called["auth"] == ("u", "t")
    assert called["headers"] == conn.headers
    assert called["json"] == {"transition": {"id": "55"}}


def test_jira_add_comment_calls_requests_post_with_adf_payload(monkeypatch):
    called = {}
    response = SimpleNamespace(status_code=201)

    def fake_post(url, auth, headers, json):
        called["url"] = url
        called["auth"] = auth
        called["headers"] = headers
        called["json"] = json
        return response

    monkeypatch.setattr(jira.requests, "post", fake_post)
    conn = jira.JiraConnection("https://example.atlassian.net", "u", "t")

    out = conn.add_comment("PROJ-4", "Hello world")

    assert out is response
    assert called["url"].endswith("/issue/PROJ-4/comment")
    assert called["auth"] == ("u", "t")
    assert called["headers"] == conn.headers
    assert called["json"]["body"]["type"] == "doc"
    assert called["json"]["body"]["content"][0]["content"][0]["text"] == "Hello world"


def test_jira_find_transition_id_returns_none_on_non_200(monkeypatch):
    conn = jira.JiraConnection("https://example.atlassian.net", "u", "t")
    monkeypatch.setattr(
        conn,
        "get_transitions",
        lambda _key: SimpleNamespace(status_code=500, json=lambda: {}),
    )

    assert conn.find_transition_id("PROJ-5", "Done") is None


def test_jira_find_transition_id_matches_transition_name(monkeypatch):
    conn = jira.JiraConnection("https://example.atlassian.net", "u", "t")
    monkeypatch.setattr(
        conn,
        "get_transitions",
        lambda _key: SimpleNamespace(
            status_code=200,
            json=lambda: {"transitions": [{"id": "12", "name": "Done"}]},
        ),
    )

    assert conn.find_transition_id("PROJ-5", "done") == "12"


def test_jira_find_transition_id_matches_to_name(monkeypatch):
    conn = jira.JiraConnection("https://example.atlassian.net", "u", "t")
    monkeypatch.setattr(
        conn,
        "get_transitions",
        lambda _key: SimpleNamespace(
            status_code=200,
            json=lambda: {
                "transitions": [{"id": "34", "name": "X", "to": {"name": "In Review"}}]
            },
        ),
    )

    assert conn.find_transition_id("PROJ-5", "in review") == "34"


def test_jira_find_transition_id_returns_none_when_missing(monkeypatch):
    conn = jira.JiraConnection("https://example.atlassian.net", "u", "t")
    monkeypatch.setattr(
        conn,
        "get_transitions",
        lambda _key: SimpleNamespace(
            status_code=200, json=lambda: {"transitions": [{"id": "1", "name": "Todo"}]}
        ),
    )

    assert conn.find_transition_id("PROJ-5", "Done") is None


def test_jira_transition_to_status_handles_no_transition(monkeypatch):
    conn = jira.JiraConnection("https://example.atlassian.net", "u", "t")
    monkeypatch.setattr(conn, "find_transition_id", lambda *_args: None)

    ok, msg = conn.transition_to_status("PROJ-1", "Done")

    assert not ok
    assert msg == "No transition found to status 'Done'"


def test_jira_transition_to_status_success(monkeypatch):
    conn = jira.JiraConnection("https://example.atlassian.net", "u", "t")
    monkeypatch.setattr(conn, "find_transition_id", lambda *_args: "77")
    monkeypatch.setattr(
        conn,
        "transition_issue",
        lambda *_args: SimpleNamespace(status_code=204, text=""),
    )

    ok, msg = conn.transition_to_status("PROJ-1", "Done")

    assert ok
    assert msg == "Transitioned PROJ-1 to Done"


def test_jira_transition_to_status_failure(monkeypatch):
    conn = jira.JiraConnection("https://example.atlassian.net", "u", "t")
    monkeypatch.setattr(conn, "find_transition_id", lambda *_args: "77")
    monkeypatch.setattr(
        conn,
        "transition_issue",
        lambda *_args: SimpleNamespace(status_code=400, text="bad transition"),
    )

    ok, msg = conn.transition_to_status("PROJ-1", "Done")

    assert not ok
    assert msg == "Failed to transition: bad transition"
