# FLAFL

[![PyPI](https://img.shields.io/pypi/v/flafl.svg)](https://pypi.org/project/flafl/)
[![Changelog](https://img.shields.io/github/v/release/msleigh/flafl?include_prereleases&label=changelog)](https://github.com/msleigh/flafl/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/msleigh/flafl/blob/main/LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)

Flask application for listening to webhooks

Listens for events triggered by GitHub webhooks and updates Jira tickets
accordingly. Automatically transitions Jira issues when pull requests are
opened, merged, or reviewed.

---

## Features

- **Automatic Jira transitions**: Move tickets to "In Review" when PRs are opened, "Done" when merged
- **Jira key extraction**: Finds Jira issue keys in PR titles, branch names, and descriptions
- **Missing ticket detection**: Comments on PRs that don't reference a Jira ticket
- **PR review handling**: Optionally transition tickets based on review status
- **Configurable workflow**: Map PR events to your Jira workflow statuses

## Requirements

FLAFL requires Python 3.8+. It is tested on Linux and macOS.

You need:
- A Jira Cloud instance with API access
- A GitHub repository with webhook permissions
- A server to host the webhook endpoint

## Installation

FLAFL is published as a Python package and can be installed with `pip`,
ideally by using a virtual environment. Open up a terminal and install with:

    pip install flafl

## Configuration

Export the following environment variables:

### Required

```bash
# Jira Configuration
export JIRA_BASE_URL="https://your-org.atlassian.net"
export JIRA_USER_EMAIL="your-email@example.com"
export JIRA_API_TOKEN="your-jira-api-token"

# GitHub Configuration
export GITHUB_TOKEN="your-github-token"
```

### Optional (Status Transitions)

```bash
# Status to transition to when PR is opened (default: "In Review")
export STATUS_ON_PR_OPENED="In Review"

# Status to transition to when PR is merged (default: "Done")
export STATUS_ON_PR_MERGED="Done"

# Status to transition to when PR is closed without merge (optional)
export STATUS_ON_PR_DECLINED="To Do"

# Status to transition to when review is approved (optional)
export STATUS_ON_REVIEW_APPROVED="Approved"

# Status to transition to when changes are requested (optional)
export STATUS_ON_CHANGES_REQUESTED="In Progress"

# Add Jira comments when PR is synchronized with new commits (default: false)
export COMMENT_ON_PR_SYNC="false"
```

### Getting API Tokens

**Jira API Token:**
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a name and copy the token

**GitHub Token:**
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo` (for private repos) or `public_repo` (for public repos)
4. Copy the token

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

In the `flafl` directory run:

    ./flafld <command>

to control the service. Specifically:

- `flafld start` or `flafld run` start the service in the background, recording
  the process ID to `${TMP:-/tmp}/.flafl.pid`
- `flafld stop` stops the process (and its children)
- `flafld restart` stops the running service and starts it again

On starting the service, the port number of the Flask application is printed.
Make a note of this for use in setting up webhooks in GitHub.

## GitHub Webhook Configuration

1. Go to your repository on GitHub
2. Navigate to **Settings** > **Webhooks** > **Add webhook**
3. Configure the webhook:
   - **Payload URL**: `https://<your-server>:8080/flafl/api/v1.0/events`
   - **Content type**: `application/json`
   - **Secret**: (optional, but recommended for production)
   - **SSL verification**: Enable if using HTTPS

4. Select events to trigger the webhook:
   - **Pull requests** (for opened, closed, merged, synchronized)
   - **Pull request reviews** (for review submitted)
   - **Issue comments** (for PR comments)
   - **Pushes** (optional, for tracking commits)

5. Click **Add webhook**

GitHub will send a ping event to verify the connection. You should see a
successful response.

## Supported Events

| GitHub Event | Action | Jira Behavior |
|--------------|--------|---------------|
| `pull_request` | `opened` | Transition to "In Review", comment if no Jira key |
| `pull_request` | `reopened` | Transition to "In Review" |
| `pull_request` | `closed` (merged) | Transition to "Done" |
| `pull_request` | `closed` (not merged) | Optionally transition back |
| `pull_request` | `synchronize` | Optionally add comment about new commits |
| `pull_request_review` | `submitted` (approved) | Optionally transition to "Approved" |
| `pull_request_review` | `submitted` (changes_requested) | Optionally transition to "In Progress" |
| `issue_comment` | `created` | Log comment (no transition) |
| `push` | - | Extract Jira keys from commit messages |
| `ping` | - | Verify webhook connection |

## Jira Key Detection

FLAFL looks for Jira issue keys (e.g., `PROJ-123`) in:

1. PR title: `PROJ-123: Add new feature`
2. Branch name: `feature/PROJ-123-add-login`
3. PR description/body

If no Jira key is found, FLAFL will add a comment to the PR asking the author
to include one.

## Health Check

A health check endpoint is available at:

    GET /flafl/api/v1.0/health

Returns:
```json
{
  "status": "healthy",
  "jira_connected": true,
  "github_connected": true
}
```

## Logging

Diagnostic output is written to `flafl.log` in the application directory:

```
2024-01-15 10:30:45.123456
Event: pull_request/opened
{
  "status": "success",
  "message": "PR #42 opened: PROJ-123: Add new feature",
  "jira_keys": ["PROJ-123"],
  "results": ["Transitioned PROJ-123 to In Review"]
}
```

## Extending FLAFL

FLAFL uses the Strategy pattern for event handling. To add a new event handler:

1. Create a new class in `strategies.py` that inherits from `Strategy`
2. Implement the `execute(self, json_data, debug_info, conns, config)` method
3. Add routing logic in `__init__.py`'s `select_strategy()` function

## Migration from Bitbucket/Bamboo

If you're migrating from the previous Bitbucket/Bamboo version:

1. Update environment variables (see Configuration section)
2. Update webhook URLs in GitHub (instead of Bitbucket)
3. Configure Jira workflow status names to match your project

The core webhook endpoint remains the same: `/flafl/api/v1.0/events`
