import datetime  # for log only
import re


def log(log_entry):
    with open(__package__ + ".log", "a") as file_pointer:
        file_pointer.write(str(datetime.datetime.now()) + "\n")
        file_pointer.write(log_entry)
        file_pointer.write("\n")


def check_for_jira_ticket(
    conns, to_ref_proj, to_ref_slug, pull_request_id, pull_request_title
):
    JIRA_TICKET_REGEX = re.compile(to_ref_proj + "-[0-9]+")
    # PR ID 1 is used for testing
    if pull_request_id != "1" and not JIRA_TICKET_REGEX.match(pull_request_title):
        comment = (
            "Please add a Jira ticket ID to the pull request title. E.g. 'JIRA-123: "
            + pull_request_title
            + "'"
        )
        try:
            conns["bitb"].post(
                "projects/"
                + to_ref_proj
                + "/repos/"
                + to_ref_slug
                + "/pull-requests/"
                + str(pull_request_id)
                + "/comments",
                json={"text": comment},
            )
        except AttributeError:
            print("ERROR: no Bitbucket connection")
