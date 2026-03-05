"""Unit tests for uncovered strategy branches."""

import flafl
from flafl import strategies


def test_strategy_abstract_execute_is_callable_for_coverage():
    assert strategies.Strategy.execute(None, None, None, None, None) is None


def test_strategy_pr_closed_declined_with_transition(monkeypatch):
    def fake_get_pr_info(_json_data, _debug_info):
        return {"number": 8, "title": "PR title"}

    monkeypatch.setattr(strategies.jsonparser, "get_pr_info", fake_get_pr_info)
    monkeypatch.setattr(
        strategies.jsonparser, "extract_jira_keys_from_pr", lambda *_args: ["PROJ-1"]
    )
    monkeypatch.setattr(strategies.jsonparser, "is_pr_merged", lambda *_args: False)
    monkeypatch.setattr(
        strategies.helpers,
        "transition_jira_issue",
        lambda *_args: (True, "transitioned"),
    )

    with flafl.app.app_context():
        rv = strategies.PrClosed().execute(
            {}, {}, {}, {"status_on_pr_declined": "To Do"}
        )
        out = rv.get_json()

    assert out["status"] == "success"
    assert out["merged"] is False
    assert out["results"] == ["transitioned"]
    assert "closed without merge" in out["message"]


def test_strategy_pr_closed_no_jira_keys(monkeypatch):
    monkeypatch.setattr(
        strategies.jsonparser,
        "get_pr_info",
        lambda *_args: {"number": 2, "title": "No key PR"},
    )
    monkeypatch.setattr(
        strategies.jsonparser, "extract_jira_keys_from_pr", lambda *_args: []
    )
    monkeypatch.setattr(strategies.jsonparser, "is_pr_merged", lambda *_args: False)

    with flafl.app.app_context():
        rv = strategies.PrClosed().execute({}, {}, {}, {})
        out = rv.get_json()

    assert out["results"] == ["No Jira keys found in PR"]
    assert "closed" in out["message"]


def test_strategy_pr_synchronize_adds_jira_comments(monkeypatch):
    monkeypatch.setattr(
        strategies.jsonparser,
        "get_pr_info",
        lambda *_args: {"number": 11, "head_sha": "abcdef012345", "title": "sync"},
    )
    monkeypatch.setattr(
        strategies.jsonparser, "extract_jira_keys_from_pr", lambda *_args: ["PROJ-7"]
    )
    monkeypatch.setattr(
        strategies.helpers, "add_jira_comment", lambda *_args: (True, "commented")
    )

    with flafl.app.app_context():
        rv = strategies.PrSynchronize().execute(
            {}, {}, {}, {"comment_on_pr_sync": True}
        )
        out = rv.get_json()

    assert out["results"] == ["commented"]
    assert out["head_sha"] == "abcdef012345"


def test_strategy_review_submitted_transitions_on_approved(monkeypatch):
    monkeypatch.setattr(
        strategies.jsonparser, "get_pr_info", lambda *_args: {"number": 4, "title": "x"}
    )
    monkeypatch.setattr(
        strategies.jsonparser,
        "get_review_info",
        lambda *_args: {"state": "approved", "user": "r"},
    )
    monkeypatch.setattr(
        strategies.jsonparser, "extract_jira_keys_from_pr", lambda *_args: ["PROJ-9"]
    )
    monkeypatch.setattr(
        strategies.helpers,
        "transition_jira_issue",
        lambda *_args: (True, "approved transition"),
    )

    with flafl.app.app_context():
        rv = strategies.PrReviewSubmitted().execute(
            {}, {}, {}, {"status_on_review_approved": "Approved"}
        )
        out = rv.get_json()

    assert out["review_state"] == "approved"
    assert out["results"] == ["approved transition"]


def test_strategy_review_submitted_transitions_on_changes_requested(monkeypatch):
    monkeypatch.setattr(
        strategies.jsonparser, "get_pr_info", lambda *_args: {"number": 6, "title": "x"}
    )
    monkeypatch.setattr(
        strategies.jsonparser,
        "get_review_info",
        lambda *_args: {"state": "changes_requested", "user": "r"},
    )
    monkeypatch.setattr(
        strategies.jsonparser, "extract_jira_keys_from_pr", lambda *_args: ["PROJ-10"]
    )
    monkeypatch.setattr(
        strategies.helpers,
        "transition_jira_issue",
        lambda *_args: (True, "changes transition"),
    )

    with flafl.app.app_context():
        rv = strategies.PrReviewSubmitted().execute(
            {}, {}, {}, {"status_on_changes_requested": "In Progress"}
        )
        out = rv.get_json()

    assert out["review_state"] == "changes_requested"
    assert out["results"] == ["changes transition"]
