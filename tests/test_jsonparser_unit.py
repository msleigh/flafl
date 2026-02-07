"""Unit tests for flafl.jsonparser error paths."""

import pytest

from flafl import exceptions
from flafl import jsonparser


def test_jsonparser_get_pr_info_missing_required_field_raises():
    payload = {
        "pull_request": {
            "number": 1,
            "title": "PROJ-1",
            "state": "open",
            "merged": False,
            "head": {"sha": "abc", "ref": "feature/PROJ-1"},
            "base": {"ref": "main", "repo": {"owner": {"login": "o"}}},
            "html_url": "https://example/p/1",
            "user": {"login": "u"},
        }
    }

    with pytest.raises(exceptions.InvalidUsage) as exc:
        jsonparser.get_pr_info(payload, {"d": 1})

    assert "Pull request payload missing required field" in exc.value.message


def test_jsonparser_get_review_info_missing_review_raises():
    with pytest.raises(exceptions.InvalidUsage) as exc:
        jsonparser.get_review_info({}, {"d": 1})

    assert exc.value.message == "Payload does not contain review key"


def test_jsonparser_get_comment_info_missing_comment_raises():
    with pytest.raises(exceptions.InvalidUsage) as exc:
        jsonparser.get_comment_info({}, {"d": 1})

    assert exc.value.message == "Payload does not contain comment key"
