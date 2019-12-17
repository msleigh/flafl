"""Helper functions for parsing JSON payloads from POST requests to the API."""

from . import exceptions

INVALID_USAGE = exceptions.InvalidUsage


def is_connection_test(json_data):
    """Check if event is just a connection test"""
    return "test" in json_data


def get_event_key(json_data, debug_info):
    """Get eventKey.

    The eventKey is the primary key that defines the event that triggered a
    webhook.
    """
    if "eventKey" not in json_data:
        message = "POST method to this endpoint must provide an eventKey"
        raise INVALID_USAGE(message, status_code=410, payload=debug_info)
    event_key = json_data["eventKey"]
    event_key_field = event_key.split(":")
    if len(event_key_field) < 2:
        message = "eventKey must contain two or more colon-separated items"
        raise INVALID_USAGE(message, status_code=410, payload=debug_info)
    event_trigger = event_key_field[1]
    return event_key, event_trigger


def verify_pull_request_id(json_data, debug_info):
    """Look for pullRequest id key."""
    try:
        pull_request_id = str(json_data["pullRequest"]["id"])
    except TypeError:
        message = "Pull request event does not contain pullRequest id key"
        raise INVALID_USAGE(message, status_code=420, payload=debug_info)
    except KeyError:
        message = "Pull request event does not contain pullRequest key"
        raise INVALID_USAGE(message, status_code=420, payload=debug_info)
    if not pull_request_id.isdigit():
        message = "Pull Request ID is not an integer"
        raise INVALID_USAGE(message, status_code=420, payload=debug_info)
    return pull_request_id


def get_from_ref_latest_commit(json_data, debug_info):
    """Get latestCommit hash for the fromRef branch."""
    try:
        from_ref_latest_commit = json_data["pullRequest"]["fromRef"]["latestCommit"]
    except KeyError:
        message = "Pull request event does not contain fromRef key"
        raise INVALID_USAGE(message, status_code=420, payload=debug_info)
    except TypeError:
        message = "Pull request fromRef does not contain latestCommit key"
        raise INVALID_USAGE(message, status_code=420, payload=debug_info)
    if not isinstance(from_ref_latest_commit, str) or len(from_ref_latest_commit) != 40:
        message = "Pull request fromRef latestCommit not a 40-character string"
        debug_info["type_of_from_ref_latest_commit"] = str(type(from_ref_latest_commit))
        debug_info["len_of_from_ref_latest_commit"] = len(from_ref_latest_commit)
        raise INVALID_USAGE(message, status_code=420, payload=debug_info)
    return from_ref_latest_commit
