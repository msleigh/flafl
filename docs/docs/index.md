# Welcome to FLAFL

**Flask application for listening to webhooks**

[![PyPI](https://img.shields.io/pypi/v/flafl.svg)](https://pypi.org/project/flafl/)
[![Changelog](https://img.shields.io/github/v/release/msleigh/flafl?include_prereleases&label=changelog)](https://github.com/msleigh/flafl/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/msleigh/flafl/blob/main/LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)

Listens for events triggered by Webhooks in an Atlassian Bitbucket
server and responds.

It assumes the main purpose is to trigger test plans in an associated Bamboo
instance, but can be persuaded to take other actions.

## Requirements

FLAFL requires Python 3.8+. It is tested on Linux and macOS.

You  must have a netrc file containing valid login details for the Bamboo
hostname used.

## Installation

FLAFL is published as a Python package and can be installed with `pip`, ideally
by using a virtual environment. Open up a terminal and install with:

    pip install flafl

## Configuration

Export the following variables with the correct information:

    export NETRC_FILE="/path/to/netrc/file"
    export BAMB_HOSTNAME="bamboo.yourorg.com"
    export BITB_HOSTNAME="bitbucket.yourorg.com"

To run the tests (see below), these environment variables must be defined,
but do not need to have the correct values.

    export BITB_PROJECT="test"
    export BITB_REPO="test"

## Tests

To set up and run tests with `uv`, run:

    uv sync --group dev
    uv run pytest

or to get test-coverage information run:

    uv run coverage run -m pytest

which allows a test-coverage report to be produced:

    uv run coverage report

or as a web page:

    uv run coverage html
    xdg-open htmlcov/index.html

## Usage

The main application runs as a background service.

In the `flafl` directory run:

    ./flafld <command>

to control the service. Specifically:

- `flafld start` or `flafld run` start the service in the background, recording
  the process ID to `${TMP:-/tmp}/.flafl.pid`
- `flafld stop` stops the process (and its children)
- `flafld restart` stops the running service and starts it again

On starting the service, the port number of the Flask application is printed.
Make a note of this for use in setting webhooks up in Bitbucket.

## Bitbucket configuration

In a browser, go to the webhook set-up page of your repository in your Bitbucket
server:

    https://<bitbucket.yourorg.com>/plugins/servlet/webhooks/projects/<project>/repos/<repo>

Create webhook by clicking "Create webhook", giving it a name (e.g. "flafl"),
and specifying the URL of your running FLAFL application, e.g.:

    https://<flafl-app-host.yourorg.com>:8080/flafl/api/v1.0/events

No "Secret" is required. Click "Test connection", and you should get a return
code of "200", and in "View details", the body of the response from the
applications should be:

    {
      "debug_info": {
        "payloadReceived": {
          "test": true
        }
      },
      "message": "Successful connection."
    }

Now select which events should send webhooks to the app. Under the
"Repository" column, the following webhooks, if selected, will trigger a respose:

- Push

and under the "Pull request" column, the following:

- Opened
- Modified
- Merged
- Declined
- Deleted
- Comment added

Others will be quietly ignored. FLAFL can easily be extended to add responses
to other tiggers of interest.

Click "Save".

To test the Bitbucket configuration, create a new pull request (the target
branch must be within the repository that has the webhooks; the source branch
can be outside, e.g. in a fork).

In the directory containing the FLAFL application code, a log file should have been
created with some diagnostic output, e.g.:

    2019-12-17 17:18:54.360661
    Success payload:
    {
        "message": "Created PR with ID 321 from project/repo/feature-branch to project/repo/develop. Sent API call to Bamboo and got return code 204",
        "status": "success"
    }

Also, the application should have automatically added a comment to the PR
asking the PR author to add a Jira ticket ID to the PR title. This is an
example of the kind of checks the application can perform.

Adding a comment to the PR, and deleting or declining the PR, should also add
similar diagnostic output to the `flafl.log` file.
