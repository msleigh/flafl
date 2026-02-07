"""Coverage-focused tests for flafl.__init__."""

import importlib

import flafl


ENDPOINT = "/flafl/api/v1.0/events"


def _set_required_env(monkeypatch):
    monkeypatch.setenv("JIRA_BASE_URL", "https://example.atlassian.net")
    monkeypatch.setenv("JIRA_USER_EMAIL", "user@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "token")
    monkeypatch.setenv("GITHUB_TOKEN", "gh-token")


def test_init_creates_connections_when_env_present(monkeypatch):
    """Exercise the successful connection setup branches during module import."""
    _set_required_env(monkeypatch)

    jira_conn = object()
    github_conn = object()

    monkeypatch.setattr(flafl.jira, "JiraConnection", lambda *args: jira_conn)
    monkeypatch.setattr(flafl.github, "GitHubConnection", lambda *args: github_conn)

    reloaded = importlib.reload(flafl)
    assert reloaded.conns["jira"] is jira_conn
    assert reloaded.conns["github"] is github_conn


def test_init_handles_connection_setup_errors(monkeypatch, capsys):
    """Exercise exception handlers around connection setup during import."""
    _set_required_env(monkeypatch)

    def raise_jira(*_args, **_kwargs):
        raise RuntimeError("jira boom")

    def raise_github(*_args, **_kwargs):
        raise RuntimeError("github boom")

    monkeypatch.setattr(flafl.jira, "JiraConnection", raise_jira)
    monkeypatch.setattr(flafl.github, "GitHubConnection", raise_github)

    reloaded = importlib.reload(flafl)
    output = capsys.readouterr().out

    assert "ERROR: Failed to create Jira connection: jira boom" in output
    assert "ERROR: Failed to create GitHub connection: github boom" in output
    assert reloaded.conns["jira"] is None
    assert reloaded.conns["github"] is None


def test_post_event_ignores_logging_type_errors(monkeypatch):
    """Exercise the TypeError/AttributeError guard around helpers.log."""
    flafl.app.config["TESTING"] = True
    client = flafl.app.test_client()

    def raise_type_error(_msg):
        raise TypeError("log failed")

    monkeypatch.setattr(flafl.helpers, "log", raise_type_error)

    rv = client.post(
        ENDPOINT,
        json={"ref": "refs/heads/main", "commits": [], "repository": {"name": "repo"}},
        headers={"X-GitHub-Event": "push"},
    )

    assert rv.status_code == 200
    assert rv.get_json()["status"] == "success"


def test_select_strategy_unhandled_review_and_comment_actions():
    """Exercise unhandled action branches for review/comment event types."""
    review_strategy = flafl.select_strategy("pull_request_review", "edited")
    comment_strategy = flafl.select_strategy("issue_comment", "deleted")

    assert isinstance(review_strategy, flafl.strategies.Unhandled)
    assert isinstance(comment_strategy, flafl.strategies.Unhandled)
