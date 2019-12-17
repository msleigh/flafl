"""
Tests for the .

These tests simulate how the program behaves when a repository payload is provided.

"""
import pytest
import flafl


endpoint = "/flafl/api/v1.0/events"


@pytest.fixture
def client():
    flafl.app.config["TESTING"] = True
    client = flafl.app.test_client()
    yield client


def test_notCodedYet_3(client):
    rv = client.post(endpoint, json={"eventKey": "repo:anything"})
    json_data = rv.get_json()
    assert json_data["message"] == "Trigger-handling for eventKey not coded yet"
