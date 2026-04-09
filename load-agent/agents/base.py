from abc import ABC

import requests
from settings import Settings


class BaseAgent(ABC):
    """
    Base class for all ACA-Py agents. Provides common HTTP client functionality
    for interacting with the agent's admin API.

    Subclasses must set `agent_url` and `headers` in their `__init__` to point
    to the correct agent's admin interface.
    """

    def __init__(self):
        self.agent_url = Settings.ISSUER_URL
        self.headers = Settings.ISSUER_HEADERS | {"Content-Type": "application/json"}

    def get_invite(self):
        """
        Creates an out-of-band invitation and returns the invitation URL and connection ID.

        Returns:
            dict: Contains 'invitation_url' and 'connection_id' for establishing a connection.
        """
        r = requests.post(
            f"{self.agent_url}/out-of-band/create-invitation?auto_accept=true",
            json={"handshake_protocols": Settings.HANDSHAKE_PROTOCOLS},
            headers=self.headers,
        )
        invitation = r.json()

        r = requests.get(
            f"{self.agent_url}/connections",
            params={"invitation_msg_id": invitation["invi_msg_id"]},
            headers=self.headers,
        )
        connection = r.json()["results"][0]

        return {
            "invitation_url": invitation["invitation_url"],
            "connection_id": connection["connection_id"],
        }

    def is_up(self):
        """
        Checks if the agent's admin interface is reachable and responding.

        Returns:
            bool: True if agent is up, False otherwise.
        """
        try:
            r = requests.get(
                f"{self.agent_url}/status",
                headers=self.headers,
            )
            if r.status_code != 200:
                raise Exception(r.content)

            r.json()
        except Exception:
            return False

        return True

    def send_message(self, connection_id, msg):
        """
        Sends a basic message to a connected agent via the connections protocol.

        Args:
            connection_id (str): The established connection ID to send the message to.
            msg (str): The message content to send.
        """
        requests.post(
            f"{self.agent_url}/connections/{connection_id}/send-message",
            json={"content": msg},
            headers=self.headers,
        )
