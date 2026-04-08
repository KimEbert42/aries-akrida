from abc import abstractmethod

from settings import Settings

from ..base import BaseAgent


class BaseHolder(BaseAgent):
    def __init__(self):
        super().__init__()
        self.label = "Test Holder"
        self.agent_url = Settings.HOLDER_URL
        self.headers = Settings.HOLDER_HEADERS | {"Content-Type": "application/json"}

    @abstractmethod
    def accept_invite(self, invitation_url, use_connection_did=False):
        pass

    @abstractmethod
    def receive_credential_prepare(self):
        pass

    @abstractmethod
    def receive_credential(self):
        pass

    @abstractmethod
    def presentation_exchange_prepare(self):
        pass

    @abstractmethod
    def presentation_exchange(self):
        pass

    @abstractmethod
    def ping_mediator(self):
        pass

    @abstractmethod
    def delete_oob(self, id):
        pass

    @abstractmethod
    def receive_message_prepare(self):
        pass

    @abstractmethod
    def receive_message(self):
        pass