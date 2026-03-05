"""Unit tests for flafl.github."""

from types import SimpleNamespace

from flafl import github


def test_github_connection_init_sets_headers():
    conn = github.GitHubConnection("token-123")

    assert conn.token == "token-123"
    assert conn.api_url == "https://api.github.com"
    assert conn.headers["Authorization"] == "Bearer token-123"
    assert conn.headers["Accept"] == "application/vnd.github+json"
    assert conn.headers["X-GitHub-Api-Version"] == "2022-11-28"


def test_github_add_pr_comment_calls_requests_post(monkeypatch):
    called = {}
    response = SimpleNamespace(status_code=201)

    def fake_post(url, headers, json):
        called["url"] = url
        called["headers"] = headers
        called["json"] = json
        return response

    monkeypatch.setattr(github.requests, "post", fake_post)
    conn = github.GitHubConnection("abc")

    out = conn.add_pr_comment("octo", "repo", 7, "hello")

    assert out is response
    assert called["url"].endswith("/repos/octo/repo/issues/7/comments")
    assert called["headers"] == conn.headers
    assert called["json"] == {"body": "hello"}


def test_github_get_pr_calls_requests_get(monkeypatch):
    called = {}
    response = SimpleNamespace(status_code=200)

    def fake_get(url, headers):
        called["url"] = url
        called["headers"] = headers
        return response

    monkeypatch.setattr(github.requests, "get", fake_get)
    conn = github.GitHubConnection("abc")

    out = conn.get_pr("octo", "repo", 99)

    assert out is response
    assert called["url"].endswith("/repos/octo/repo/pulls/99")
    assert called["headers"] == conn.headers


def test_github_get_pr_commits_calls_requests_get(monkeypatch):
    called = {}
    response = SimpleNamespace(status_code=200)

    def fake_get(url, headers):
        called["url"] = url
        called["headers"] = headers
        return response

    monkeypatch.setattr(github.requests, "get", fake_get)
    conn = github.GitHubConnection("abc")

    out = conn.get_pr_commits("octo", "repo", 99)

    assert out is response
    assert called["url"].endswith("/repos/octo/repo/pulls/99/commits")
    assert called["headers"] == conn.headers
