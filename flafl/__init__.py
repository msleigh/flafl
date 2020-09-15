"""
Main package.

Define the end points of the REST API; delegate responses to strategies
"""
import json
import os

from flask import Flask, jsonify, request

from . import bamboo
from . import context
from . import helpers
from . import strategies
from . import exceptions
from . import jsonparser

USER_HOME = os.environ["HOME"]

try:
    NETRC_FILE = os.environ["NETRC_FILE"]
except KeyError:
    print("ERROR: Location of netrc file for Bamboo credentials not specified")
    NETRC_FILE = None

try:
    BAMB_HOSTNAME = os.environ["BAMB_HOSTNAME"]
except KeyError:
    print("ERROR: Bamboo hostname not specified")
    BAMB_HOSTNAME = None

try:
    BITB_HOSTNAME = os.environ["BITB_HOSTNAME"]
except KeyError:
    print("ERROR: Bitbucket hostname not specified")
    BITB_HOSTNAME = None

try:
    BITB_PROJECT = os.environ["BITB_PROJECT"]
except KeyError:
    print("ERROR: Bitbucket project name not specified")
    BITB_PROJECT = None

try:
    BITB_REPO = os.environ["BITB_REPO"]
except KeyError:
    print("ERROR: Bitbucket repository name not specified")
    BITB_REPO = None

conns = {}
try:
    conns["bamb"] = bamboo.BambooConnection(NETRC_FILE, BAMB_HOSTNAME)
except FileNotFoundError:
    print("ERROR: netrc file not found")
    conns["bamb"] = None

try:
    conns["bitb"] = bamboo.BambooConnection(NETRC_FILE, BITB_HOSTNAME)
except FileNotFoundError:
    print("ERROR: netrc file not found")
    conns["bitb"] = None

## TODO: temporary checks until in routine use --------------------------------
## Check contact with Bamboo. (Just make a simple GET API call that lists all projects.)
# response = conns["bamb"].get("project.json")
# assert response.status_code == 200
# helpers.log(json.dumps(response.json(), sort_keys=True, indent=4))
## Check contact with Bitbucket. (Just make a simple GET API call that lists all projects.)
# response = conns["bitb"].get("projects", apiversion="1.0")
# assert response.status_code == 200
# helpers.log(json.dumps(response.json(), sort_keys=True, indent=4))
# ----------------------------------------------------------------------------


app = Flask(__name__)


@app.errorhandler(exceptions.InvalidUsage)
def handle_invalid_usage(error):
    """Error handler for InvalidUsage exception."""
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/flafl/api/v1.0/events", methods=["POST"])
def post_event():

    debug_info = {}
    debug_info["payloadReceived"] = request.json

    # Verbose
    # helpers.log(json.dumps(request.json, sort_keys=True, indent=4))

    # For 'Test Connection' function in Bamboo webhook settings
    if jsonparser.is_connection_test(request.json):
        message = "Successful connection."
        return jsonify({"message": message, "debug_info": debug_info})

    event_key, event_trigger = jsonparser.get_event_key(request.json, debug_info)

    debug_info["eventKey"] = event_key
    debug_info["eventTrigger"] = event_trigger

    # Select the appropriate strategy
    if event_key.startswith("pr:"):

        if event_trigger == "opened":
            concrete_strategy = strategies.PrCreate()

        if event_trigger == "deleted":
            concrete_strategy = strategies.PrDestroy()

        if event_trigger == "merged":
            concrete_strategy = strategies.PrDestroy()

        if event_trigger == "declined":
            concrete_strategy = strategies.PrDestroy()

        if event_trigger == "modified":
            concrete_strategy = strategies.PrModify()

        if event_trigger == "comment":
            concrete_strategy = strategies.PrComment()

    if event_key.startswith("repo:"):

        if event_trigger == "refs_changed":
            concrete_strategy = strategies.RepoPush()

        else:
            concrete_strategy = strategies.RepoAll()

    # Execute the strategy
    try:
        ct = context.Context(concrete_strategy)
    except UnboundLocalError:
        message = "Trigger-handling for eventKey not coded yet"
        payload = {"eventKey": event_key}
        success_payload = {"message": message, "payload": payload}
    else:
        return_value = ct.execute_strategy(request.json, debug_info, conns)
        success_payload = return_value.get_json()

    try:
        helpers.log(
            "Success payload:\n" + json.dumps(success_payload, sort_keys=True, indent=4)
        )
    except TypeError:
        pass

    return jsonify(success_payload)
