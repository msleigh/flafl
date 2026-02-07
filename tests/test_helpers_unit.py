"""Unit tests for flafl.helpers."""

from types import SimpleNamespace

from flafl import helpers


def test_add_missing_jira_comment_no_github_connection(monkeypatch):
    logs = []
    monkeypatch.setattr(helpers, "log", logs.append)

    helpers.add_missing_jira_comment(
        {}, {"repo_owner": "o", "repo_name": "r", "number": 1}
    )

    assert logs == ["ERROR: No GitHub connection - cannot add comment"]


def test_add_missing_jira_comment_success(monkeypatch):
    logs = []
    monkeypatch.setattr(helpers, "log", logs.append)

    class GH:
        def add_pr_comment(self, owner, repo, number, text):
            assert owner == "o"
            assert repo == "r"
            assert number == 5
            assert "doesn't appear to reference a Jira ticket" in text
            return SimpleNamespace(status_code=201, text="created")

    helpers.add_missing_jira_comment(
        {"github": GH()},
        {"repo_owner": "o", "repo_name": "r", "number": 5, "title": "t"},
    )

    assert logs[-1] == "Added missing Jira comment to PR #5"


def test_add_missing_jira_comment_non_201(monkeypatch):
    logs = []
    monkeypatch.setattr(helpers, "log", logs.append)

    class GH:
        def add_pr_comment(self, *_args):
            return SimpleNamespace(status_code=400, text="bad request")

    helpers.add_missing_jira_comment(
        {"github": GH()},
        {"repo_owner": "o", "repo_name": "r", "number": 5, "title": "t"},
    )

    assert logs[-1] == "Failed to add comment: 400 - bad request"


def test_add_missing_jira_comment_exception(monkeypatch):
    logs = []
    monkeypatch.setattr(helpers, "log", logs.append)

    class GH:
        def add_pr_comment(self, *_args):
            raise RuntimeError("boom")

    helpers.add_missing_jira_comment(
        {"github": GH()},
        {"repo_owner": "o", "repo_name": "r", "number": 5, "title": "t"},
    )

    assert "ERROR adding comment to PR: boom" in logs[-1]


def test_transition_jira_issue_no_connection(monkeypatch):
    logs = []
    monkeypatch.setattr(helpers, "log", logs.append)

    ok, msg = helpers.transition_jira_issue({}, "PROJ-1", "Done", {})

    assert not ok
    assert msg == "No Jira connection - cannot transition PROJ-1"
    assert logs[-1] == "ERROR: No Jira connection - cannot transition PROJ-1"


def test_transition_jira_issue_success(monkeypatch):
    logs = []
    monkeypatch.setattr(helpers, "log", logs.append)

    class JiraConn:
        def __init__(self):
            self.comment_calls = []

        def add_comment(self, issue_key, comment):
            self.comment_calls.append((issue_key, comment))

        def transition_to_status(self, issue_key, target_status):
            return True, f"{issue_key} -> {target_status}"

    jira_conn = JiraConn()
    ok, msg = helpers.transition_jira_issue(
        {"jira": jira_conn},
        "PROJ-2",
        "In Review",
        {"html_url": "https://x", "number": 9, "title": "T"},
    )

    assert ok
    assert msg == "PROJ-2 -> In Review"
    assert (
        jira_conn.comment_calls
        and "transitioning to In Review" in jira_conn.comment_calls[0][1]
    )
    assert logs[-1] == "Jira transition for PROJ-2: PROJ-2 -> In Review"


def test_transition_jira_issue_comment_exception_then_transition(monkeypatch):
    logs = []
    monkeypatch.setattr(helpers, "log", logs.append)

    class JiraConn:
        def add_comment(self, *_args):
            raise RuntimeError("comment failed")

        def transition_to_status(self, issue_key, target_status):
            return True, f"{issue_key}:{target_status}"

    ok, msg = helpers.transition_jira_issue(
        {"jira": JiraConn()},
        "PROJ-3",
        "Done",
        {"html_url": "", "number": 1, "title": "title"},
    )

    assert ok
    assert msg == "PROJ-3:Done"
    assert any(
        "Warning: Could not add comment to PROJ-3: comment failed" in line
        for line in logs
    )


def test_transition_jira_issue_transition_exception(monkeypatch):
    logs = []
    monkeypatch.setattr(helpers, "log", logs.append)

    class JiraConn:
        def add_comment(self, *_args):
            return None

        def transition_to_status(self, *_args):
            raise RuntimeError("transition failed")

    ok, msg = helpers.transition_jira_issue(
        {"jira": JiraConn()},
        "PROJ-4",
        "Done",
        {"html_url": "", "number": 1, "title": "title"},
    )

    assert not ok
    assert msg == "Failed to transition PROJ-4: transition failed"
    assert logs[-1] == "ERROR: Failed to transition PROJ-4: transition failed"


def test_add_jira_comment_no_connection(monkeypatch):
    logs = []
    monkeypatch.setattr(helpers, "log", logs.append)

    ok, msg = helpers.add_jira_comment({}, "PROJ-1", "note")

    assert not ok
    assert msg == "No Jira connection - cannot add comment to PROJ-1"
    assert logs[-1] == "ERROR: No Jira connection - cannot add comment to PROJ-1"


def test_add_jira_comment_success(monkeypatch):
    logs = []
    monkeypatch.setattr(helpers, "log", logs.append)

    class JiraConn:
        def add_comment(self, *_args):
            return SimpleNamespace(status_code=201)

    ok, msg = helpers.add_jira_comment({"jira": JiraConn()}, "PROJ-1", "note")

    assert ok
    assert msg == "Added comment to PROJ-1"
    assert logs[-1] == "Added comment to PROJ-1"


def test_add_jira_comment_non_201(monkeypatch):
    logs = []
    monkeypatch.setattr(helpers, "log", logs.append)

    class JiraConn:
        def add_comment(self, *_args):
            return SimpleNamespace(status_code=400)

    ok, msg = helpers.add_jira_comment({"jira": JiraConn()}, "PROJ-1", "note")

    assert not ok
    assert msg == "Failed to add comment to PROJ-1: 400"
    assert logs[-1] == "ERROR: Failed to add comment to PROJ-1: 400"


def test_add_jira_comment_exception(monkeypatch):
    logs = []
    monkeypatch.setattr(helpers, "log", logs.append)

    class JiraConn:
        def add_comment(self, *_args):
            raise RuntimeError("oops")

    ok, msg = helpers.add_jira_comment({"jira": JiraConn()}, "PROJ-1", "note")

    assert not ok
    assert msg == "Failed to add comment to PROJ-1: oops"
    assert logs[-1] == "ERROR: Failed to add comment to PROJ-1: oops"
