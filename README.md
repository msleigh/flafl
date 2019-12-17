# FLAFL

<h2 align="center">Flask Application For Listening...</h2>

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)

Listens for events (those triggered by Webhooks in an Atlassian Bitbucket
server) and responds.

---

## Requirements

- User must have a netrc file containing valid login details for the Bamboo
  hostname used

## Installation

    git clone .../flafl.git
    cd flafl
    python3 -m venv /path/to/virtual/environment
    source /path/to/virtual/environment/bin/activate
    pip3 install -r requirements.txt

## Local configuration

Export the following variables with the correct information:

    export NETRC_FILE="/path/to/netrc/file"
    export BAMB_HOSTNAME="bamboo.yourorg.com"
    export BITB_HOSTNAME="bitbucket.yourorg.com"

To run the tests (see below), these environment variables must be defined,
but do not need to have the correct values.

    export BITB_PROJECT="test"
    export BITB_REPO="test"

## Tests

To check set-up, run:

    python3 -m pytest

or to get test-coverage information run:

    coverage run -m pytest

which allows a test-coverage report to be produced:

    coverage report

or as a web page:

    coverage html
    xdg-open htmlcov/index.html

## Usage

The main application runs as a background service.

Use:

    ./flafld <command>

to control the service. Specifically:

- `flafld start` or `flafld run` start the service in the background, recording
  the process ID to `${TMP:-/tmp}/.flafl.pid`
- `flafld stop` stops the process (and its children)
- `flafld restart` stops the running service and starts it again

On starting the service, the port of the Flask application is printed. Make a
note of this for use in setting webhooks up in Bitbucket.

## Bitbucket configuration

In a browser go to:

    http://<bitbucket.yourorg.com>/plugins/servlet/webhooks/projects/<project>/repos/<repo>

Create webhook by clicking "Create webhook", giving it a name (e.g. "flafl"),
and the URL of your running application, e.g.:

    http://<apphost.yourorg.com>:8080/flafl/api/v1.0/events

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
"Repository" column, the following are available:

- Push

Under the "Pull request" column, the following are available:

- Opened
- Modified
- Merged
- Declined
- Deleted
- Comment added

Others will be ignored. The application can easily be extended to add others.

Click "Save".

To test the Bitbucket configuration, create a new pull request (the target
branch must be within the repository that has the webhooks; the source branch
could be outside, e.g. in a fork).

In the directory containing the application code, a log file should have been
created with some diagnostic output, e.g.:

    2019-12-17 17:18:54.360661
    Success payload:
    {
        "message": "Created PR with ID 321 from project/repo/feature-branch to project/repo/develop. Sent API call to Bamboo and got return code 204",
        "status": "success"
    }

Also, the application should have also automatically added a comment to the PR
asking the PR author to add a Jira ticket ID to the PR title. This is an
example of the kind of checks the application could perform.

Adding a comment to the PR, and deleting or declining the PR, should also add
similar diagnostic output to the `flafl.log` file.
