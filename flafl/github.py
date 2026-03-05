"""GitHub API client for interacting with pull requests."""

import requests


class GitHubConnection:
    """Connection to GitHub API."""

    def __init__(self, token):
        """
        Create the connection using a GitHub token.

        Args:
            token: GitHub personal access token or GitHub App token
        """
        self.token = token
        self.api_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def add_pr_comment(self, owner, repo, pr_number, comment_text):
        """
        Add a comment to a pull request.

        Args:
            owner: Repository owner (user or organization)
            repo: Repository name
            pr_number: Pull request number
            comment_text: Comment text to add

        Returns:
            Response object with created comment
        """
        response = requests.post(
            url=f"{self.api_url}/repos/{owner}/{repo}/issues/{pr_number}/comments",
            headers=self.headers,
            json={"body": comment_text},
        )
        return response

    def get_pr(self, owner, repo, pr_number):
        """
        Get pull request details.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number

        Returns:
            Response object with PR data
        """
        response = requests.get(
            url=f"{self.api_url}/repos/{owner}/{repo}/pulls/{pr_number}",
            headers=self.headers,
        )
        return response

    def get_pr_commits(self, owner, repo, pr_number):
        """
        Get commits in a pull request.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number

        Returns:
            Response object with commit list
        """
        response = requests.get(
            url=f"{self.api_url}/repos/{owner}/{repo}/pulls/{pr_number}/commits",
            headers=self.headers,
        )
        return response
