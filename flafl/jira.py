"""Jira API client for transitioning issues."""

import requests


class JiraConnection:
    """Connection to Jira Cloud for API calls."""

    def __init__(self, base_url, email, api_token):
        """
        Create the connection using email and API token.

        Args:
            base_url: Jira instance URL (e.g., https://your-org.atlassian.net)
            email: User email for authentication
            api_token: Jira API token (generate at https://id.atlassian.com/manage-profile/security/api-tokens)
        """
        self.auth = (email, api_token)
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/rest/api/3"
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def get_issue(self, issue_key):
        """
        Get issue details.

        Args:
            issue_key: Jira issue key (e.g., PROJ-123)

        Returns:
            Response object with issue data
        """
        response = requests.get(
            url=f"{self.api_url}/issue/{issue_key}",
            auth=self.auth,
            headers=self.headers,
        )
        return response

    def get_transitions(self, issue_key):
        """
        Get available transitions for an issue.

        Args:
            issue_key: Jira issue key (e.g., PROJ-123)

        Returns:
            Response object with available transitions
        """
        response = requests.get(
            url=f"{self.api_url}/issue/{issue_key}/transitions",
            auth=self.auth,
            headers=self.headers,
        )
        return response

    def transition_issue(self, issue_key, transition_id):
        """
        Transition an issue to a new status.

        Args:
            issue_key: Jira issue key (e.g., PROJ-123)
            transition_id: ID of the transition to execute

        Returns:
            Response object (204 on success)
        """
        payload = {"transition": {"id": str(transition_id)}}
        response = requests.post(
            url=f"{self.api_url}/issue/{issue_key}/transitions",
            auth=self.auth,
            headers=self.headers,
            json=payload,
        )
        return response

    def add_comment(self, issue_key, comment_text):
        """
        Add a comment to an issue.

        Args:
            issue_key: Jira issue key (e.g., PROJ-123)
            comment_text: Comment text to add

        Returns:
            Response object with created comment
        """
        # Jira Cloud uses Atlassian Document Format (ADF) for comments
        payload = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": comment_text}],
                    }
                ],
            }
        }
        response = requests.post(
            url=f"{self.api_url}/issue/{issue_key}/comment",
            auth=self.auth,
            headers=self.headers,
            json=payload,
        )
        return response

    def find_transition_id(self, issue_key, target_status):
        """
        Find the transition ID for a target status name.

        Args:
            issue_key: Jira issue key
            target_status: Name of the target status (e.g., "In Review", "Done")

        Returns:
            Transition ID if found, None otherwise
        """
        response = self.get_transitions(issue_key)
        if response.status_code != 200:
            return None

        transitions = response.json().get("transitions", [])
        for transition in transitions:
            if transition["name"].lower() == target_status.lower():
                return transition["id"]
            # Also check the target status name
            if transition.get("to", {}).get("name", "").lower() == target_status.lower():
                return transition["id"]
        return None

    def transition_to_status(self, issue_key, target_status):
        """
        Transition an issue to a target status by name.

        Args:
            issue_key: Jira issue key
            target_status: Name of the target status

        Returns:
            Tuple of (success: bool, message: str)
        """
        transition_id = self.find_transition_id(issue_key, target_status)
        if transition_id is None:
            return False, f"No transition found to status '{target_status}'"

        response = self.transition_issue(issue_key, transition_id)
        if response.status_code == 204:
            return True, f"Transitioned {issue_key} to {target_status}"
        else:
            return False, f"Failed to transition: {response.text}"
