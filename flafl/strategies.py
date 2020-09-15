import abc
import yaml
from flask import jsonify

# import subprocess

from . import exceptions
from . import helpers
from . import jsonparser

INVALID_USAGE = exceptions.InvalidUsage


class Strategy:
    """
    Declare an interface common to all supported algorithms. Context
    uses this interface to call the algorithm defined by a
    concrete strategy.
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def execute(self, json_data, debug_info, conns):
        pass


class PrCreate(Strategy):
    """Class for pull-request creation response."""

    def execute(self, json_data, debug_info, conns):

        jsonparser.verify_pull_request_id(json_data, debug_info)

        # Get the required info from the PR webhook payload
        pull_request_id = json_data["pullRequest"]["id"]
        pull_request_title = json_data["pullRequest"]["title"]
        to_ref_slug = json_data["pullRequest"]["toRef"]["repository"]["slug"]
        to_ref_proj = json_data["pullRequest"]["toRef"]["repository"]["project"]["key"]

        # Run basic checks on the pull request
        helpers.check_for_jira_ticket(
            conns, to_ref_proj, to_ref_slug, pull_request_id, pull_request_title
        )

        # Add the new plan (for this PR) to the Bamboo specs
        specs = {
            "version": 2,
            "plan": {
                "project-key": "bamboo-specs-repo",
                "key": to_ref_slug + str(pull_request_id),
                "name": pull_request_title,
            },
            "stages": [{"Stage 1": {"jobs": ["Job 1"]}}],
            "Job 1": {"tasks": [{"script": ["echo 'Test YAML spec'"]}]},
        }
        helpers.log(yaml.dump(specs, default_flow_style=False))

        # Trigger the scan of the Bamboo specs repo
        try:
            response = conns["bamb"].get("project/bamboo-specs-repo/repository")
            api_message = "API call to Bamboo not made."
        except AttributeError:
            print("ERROR: cannot scan Bamboo specs repository")
            api_message = "API call to Bamboo not made."
        else:
            helpers.log(
                "Repos with access to create plans in project bamboo-specs-repo:\n"
                + response.text
            )
            response = conns["bamb"].post(
                "repository/scan?repositoryName=test_bamboo_specs"
            )
            helpers.log("Response from Bamboo scan:\n" + response.text)
            response = conns["bamb"].post("repository/scan?repositoryId=2673")
            helpers.log("Response from Bamboo scan:\n" + response.text)
            api_message = "Sent API call to Bamboo and got return code " + str(
                response.status_code
            )

        message = (
            "Created PR with ID "
            + str(pull_request_id)
            + " from "
            + json_data["pullRequest"]["fromRef"]["repository"]["project"]["key"]
            + "/"
            + json_data["pullRequest"]["fromRef"]["repository"]["slug"]
            + "/"
            + json_data["pullRequest"]["fromRef"]["displayId"]
            + " to "
            + json_data["pullRequest"]["toRef"]["repository"]["project"]["key"]
            + "/"
            + json_data["pullRequest"]["toRef"]["repository"]["slug"]
            + "/"
            + json_data["pullRequest"]["toRef"]["displayId"]
            + ". "
            + api_message
        )

        return jsonify({"message": message, "status": "success"})


class PrDestroy(Strategy):
    """Class for pull-request closure response."""

    def execute(self, json_data, debug_info, conns):

        jsonparser.verify_pull_request_id(json_data, debug_info)

        message = (
            "Destroyed PR with ID "
            + str(json_data["pullRequest"]["id"])
            + " in repository "
            + json_data["pullRequest"]["fromRef"]["repository"]["project"]["key"]
            + "/"
            + json_data["pullRequest"]["toRef"]["repository"]["slug"]
        )
        return jsonify({"message": message, "status": "success"})


class PrModify(Strategy):
    """Class for pull-request modification response."""

    def execute(self, json_data, debug_info, conns):

        jsonparser.verify_pull_request_id(json_data, debug_info)

        pull_request_id = json_data["pullRequest"]["id"]
        pull_request_title = json_data["pullRequest"]["title"]
        to_ref_slug = json_data["pullRequest"]["toRef"]["repository"]["slug"]
        to_ref_proj = json_data["pullRequest"]["toRef"]["repository"]["project"]["key"]

        helpers.check_for_jira_ticket(
            conns, to_ref_proj, to_ref_slug, pull_request_id, pull_request_title
        )

        # Get the fromRef latestCommit
        from_ref_latest_commit = jsonparser.get_from_ref_latest_commit(
            json_data, debug_info
        )

        event_key, event_trigger = jsonparser.get_event_key(json_data, debug_info)
        message = (
            "status:"
            + "success"
            + "from_ref_latest_commit:"
            + from_ref_latest_commit
            + "eventKey:"
            + event_key
            + "pull_request_id:"
            + ""
            + "eventTrigger:"
            + event_trigger
        )
        return jsonify(
            {"message": message, "status": "success", "payload": from_ref_latest_commit}
        )


class PrComment(Strategy):
    """Class for pull-request comment responses."""

    def execute(self, json_data, debug_info, conns):
        """Strategy for pull-request comment events."""
        jsonparser.verify_pull_request_id(json_data, debug_info)

        # Check for comment field in JSON
        if "comment" not in json_data:
            message = "Payload for comment event did not contain comment key"
            debug_info["receivedPayload"] = json_data
            raise INVALID_USAGE(message, status_code=410, payload=debug_info)
        if "author" not in json_data["comment"]:
            message = "Payload for comment event did not contain author key"
            debug_info["receivedPayload"] = json_data
            raise INVALID_USAGE(message, status_code=410, payload=debug_info)
        if "name" not in json_data["comment"]["author"]:
            message = "Payload for comment event did not contain name key"
            debug_info["receivedPayload"] = json_data
            raise INVALID_USAGE(message, status_code=410, payload=debug_info)

        message = "Comment by " + json_data["comment"]["author"]["name"]

        # Do something...

        return jsonify({"message": message, "status": "success"})


class RepoPush(Strategy):
    """Class for repository-based webhook responses."""

    def execute(self, json_data, debug_info, conns):
        """Strategy for repository-based webhooks."""
        event_key, _ = jsonparser.get_event_key(json_data, debug_info)
        message = "Repository received push"
        success_payload = {
            "eventKey": event_key,
            "project": json_data["repository"]["project"]["key"],
        }
        return jsonify({"message": message, "payload": success_payload})


class RepoAll(Strategy):
    """Class for repository-based webhook responses."""

    def execute(self, json_data, debug_info, conns):
        """Strategy for repository-based webhooks."""
        event_key, _ = jsonparser.get_event_key(json_data, debug_info)
        message = "Trigger-handling for eventKey not coded yet"
        success_payload = {"eventKey": event_key}
        return jsonify({"message": message, "payload": success_payload})
