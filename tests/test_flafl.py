"""
Tests for the main program.

These tests simulate how the program behaves.

"""
import pytest
import flafl


endpoint = "/flafl/api/v1.0/events"


@pytest.fixture
def client():
    flafl.app.config["TESTING"] = True
    client = flafl.app.test_client()
    yield client


def test_connection_test(client):
    rv = client.post(endpoint, json={"test": "true"})
    json_data = rv.get_json()
    assert json_data["message"] == "Successful connection."


def test_no_eventKey(client):
    rv = client.post(endpoint, json={"a": 1})
    json_data = rv.get_json()
    assert (
        json_data["message"] == "POST method to this endpoint must provide an eventKey"
    )


def test_bad_eventKey(client):
    rv = client.post(endpoint, json={"eventKey": "1"})
    json_data = rv.get_json()
    assert (
        json_data["message"]
        == "eventKey must contain two or more colon-separated items"
    )


def test_notCodedYet_2(client):
    rv = client.post(endpoint, json={"eventKey": "anything:anything"})
    json_data = rv.get_json()
    assert json_data["message"] == "Trigger-handling for eventKey not coded yet"


class TestClass(object):
    def test_one(self):
        x = "this"
        assert "h" in x

    def test_two(self):
        x = "hello"
        assert not hasattr(x, "check")
