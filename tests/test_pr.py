"""
Tests for the .

These tests simulate how the program behaves when a pull request payload is provided.

"""
import pytest
import flafl


endpoint = "/flafl/api/v1.0/events"


@pytest.fixture
def client():
    flafl.app.config["TESTING"] = True
    client = flafl.app.test_client()
    yield client


def test_unrecognised_pr_trigger(client):
    rv = client.post(endpoint, json={"eventKey": "pr:null"})
    json_data = rv.get_json()
    assert json_data["message"] == "Trigger-handling for eventKey not coded yet"


def test_notCodedYet_1(client):
    rv = client.post(
        endpoint,
        json={
            "eventKey": "pr:notcoded",
            "pullRequest": {
                "id": 1,
                "fromRef": {"latestCommit": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"},
            },
        },
    )
    json_data = rv.get_json()
    assert json_data["message"] == "Trigger-handling for eventKey not coded yet"


# Tests for opened pull requests
# ------------------------------

def test_no_pullRequestKey(client):
    rv = client.post(endpoint, json={"eventKey": "pr:opened"})
    json_data = rv.get_json()
    assert json_data["message"] == "Pull request event does not contain pullRequest key"


def test_no_pullRequestId(client):
    rv = client.post(endpoint, json={"eventKey": "pr:opened", "pullRequest": "null"})
    json_data = rv.get_json()
    assert (
        json_data["message"] == "Pull request event does not contain pullRequest id key"
    )


def test_bad_pullRequestId(client):
    rv = client.post(
        endpoint, json={"eventKey": "pr:opened", "pullRequest": {"id": "null"}}
    )
    json_data = rv.get_json()
    assert json_data["message"] == "Pull Request ID is not an integer"


def test_valid_pr_opened(client):
    rv = client.post(
        endpoint,
        json={
            "eventKey": "pr:opened",
            "pullRequest": {
                "id": "1",
                "title": "pull request title",
                "state": "OPEN",
                "fromRef": {
                    "displayId": "feature-branch-name",
                    "repository": {"slug": "fork-name", "project": {"key": "~user"}},
                },
                "toRef": {
                    "displayId": "develop",
                    "repository": {"slug": "repo-name", "project": {"key": "project"}},
                },
            },
        },
    )
    json_data = rv.get_json()
    assert json_data["status"] == "success"
    assert (
        json_data["message"]
        == "Created PR with ID 1 from ~user/fork-name/feature-branch-name to project/repo-name/develop. Sent API call to Bamboo and got return code 204"
    )


# Tests for modified pull requests
# --------------------------------

def test_no_fromRef(client):
    rv = client.post(
        endpoint,
        json={
            "eventKey": "pr:modified",
            "pullRequest": {"id": "1", "title": "pull request title",
                "toRef": {
                    "displayId": "develop",
                    "repository": {"slug": "repo-name", "project": {"key": "project"}},
                }},
        },
    )
    json_data = rv.get_json()
    assert json_data["message"] == "Pull request event does not contain fromRef key"


def test_no_latestCommit(client):
    rv = client.post(
        endpoint,
        json={
            "eventKey": "pr:modified",
            "pullRequest": {"id": 1, "title": "pull request title", "fromRef": "null",
                "toRef": {
                    "displayId": "develop",
                    "repository": {"slug": "repo-name", "project": {"key": "project"}},
                }},
        },
    )
    json_data = rv.get_json()
    assert (
        json_data["message"] == "Pull request fromRef does not contain latestCommit key"
    )


def test_bad_latestCommit(client):
    rv = client.post(
        endpoint,
        json={
            "eventKey": "pr:modified",
            "pullRequest": {
                "id": 1,
                "title": "pull request title",
                "fromRef": {"latestCommit": "1"},
                "toRef": {
                    "displayId": "develop",
                    "repository": {"slug": "repo-name", "project": {"key": "project"}},
                },
            },
        },
    )
    json_data = rv.get_json()
    assert (
        json_data["message"]
        == "Pull request fromRef latestCommit not a 40-character string"
    )


def test_valid_pr_modified(client):
    rv = client.post(
        endpoint,
        json={
            "eventKey": "pr:modified",
            "pullRequest": {
                "id": "1",
                "fromRef": {"latestCommit": "1234567890123456789012345678901234567890"},
            },
        },
    )
    json_data = rv.get_json()
    assert json_data["status"] == "success"


def test_valid_pr_modified(client):
    rv = client.post(
        endpoint,
        json={
            "eventKey": "pr:modified",
            "pullRequest": {
                "id": "1",
                "title": "pull request title",
                "fromRef": {
                    "displayId": "feature-branch-name",
                    "latestCommit": "1234567890123456789012345678901234567890",
                    "repository": {"slug": "fork-name", "project": {"key": "~user"}},
                },
                "toRef": {
                    "displayId": "develop",
                    "repository": {"slug": "repo-name", "project": {"key": "project"}},
                },
            },
        },
    )
    json_data = rv.get_json()
    assert json_data["status"] == "success"
    assert json_data["payload"] == "1234567890123456789012345678901234567890"


# Tests for pull request comments
# -------------------------------

def test_no_comment(client):
    rv = client.post(
        endpoint, json={"eventKey": "pr:comment", "pullRequest": {"id": "1"}}
    )
    json_data = rv.get_json()
    assert (
        json_data["message"] == "Payload for comment event did not contain comment key"
    )


def test_no_author(client):
    rv = client.post(
        endpoint,
        json={
            "eventKey": "pr:comment",
            "pullRequest": {"id": "1"},
            "comment": {"a": "null"},
        },
    )
    json_data = rv.get_json()
    assert (
        json_data["message"] == "Payload for comment event did not contain author key"
    )


def test_no_name(client):
    rv = client.post(
        endpoint,
        json={
            "eventKey": "pr:comment",
            "pullRequest": {"id": "1"},
            "comment": {"author": "null"},
        },
    )
    json_data = rv.get_json()
    assert json_data["message"] == "Payload for comment event did not contain name key"


def test_valid_pr_comment_modified(client):
    rv = client.post(
        endpoint,
        json={
            "eventKey": "pr:comment:modified",
            "pullRequest": {"id": "1"},
            "comment": {"author": {"name": "xxxx"}},
        },
    )
    json_data = rv.get_json()
    assert json_data["status"] == "success"


def test_valid_pr_comment_deleted(client):
    rv = client.post(
        endpoint,
        json={
            "eventKey": "pr:comment:deleted",
            "pullRequest": {"id": "1"},
            "comment": {"author": {"name": "xxxx"}},
        },
    )
    json_data = rv.get_json()
    assert json_data["status"] == "success"


# Tests for removed pull requests
# -------------------------------

class TestPrDestroyed(object):
    def pr_destroyed(self, client, trigger):
        rv = client.post(
            endpoint,
            json={
                "eventKey": "pr:" + trigger,
                "pullRequest": {
                    "id": "1",
                    "fromRef": {
                        "displayId": "feature-branch-name",
                        "repository": {
                            "slug": "fork-name",
                            "project": {"key": "~user"},
                        },
                    },
                    "toRef": {
                        "displayId": "develop",
                        "repository": {"slug": "repo-name", "project": {"key": "project"}},
                    },
                },
            },
        )
        json_data = rv.get_json()
        assert json_data["status"] == "success"
        assert (
            json_data["message"]
            == "Destroyed PR with ID 1 in repository ~user/repo-name"
        )

    def test_valid_pr_deleted(self, client):
        trigger = "deleted"
        self.pr_destroyed(client, trigger)

    def test_valid_pr_merged(self, client):
        trigger = "merged"
        self.pr_destroyed(client, trigger)

    def test_valid_pr_declined(self, client):
        trigger = "declined"
        self.pr_destroyed(client, trigger)


