import time
from json.decoder import JSONDecodeError

import requests
from models import ProofRequest, RequestPresentationV1
from settings import Settings

from .base import BaseVerifier
from ..base_acapy import BaseAcapyAgent


class AcapyVerifier(BaseVerifier, BaseAcapyAgent):
    def __init__(self):
        super().__init__()
        self.proof_request = ProofRequest(
            name="PerfScore",
            requested_attributes={
                item["name"]: {
                    "name": item["name"],
                    "restrictions": [{"cred_def_id": self.cred_def_id}],
                } for item in Settings.CRED_ATTR
            },
            requested_predicates={},
            version="1.0",
        )

    def create_connectionless_request(self):
        # Calling verification agent

        # API call to /present-proof/create-request
        r = requests.post(
            f"{self.agent_url}/present-proof/create-request",
            json=RequestPresentationV1(
                comment="Performance Verification", proof_request=self.proof_request
            ).model_dump(),
            headers=self.headers,
        )

        try:
            if r.status_code != 200:
                raise Exception("Request was not successful: ", r.content)
            presentation_request = r.json()
        except JSONDecodeError:
            raise Exception(
                "Encountered JSONDecodeError while parsing the request: ", r.text
            )

        return presentation_request

    def request_verification(self, connection_id):
        # From verification side
        # Might need to change nonce
        # TO DO: Generalize schema parts
        r = requests.post(
            f"{self.agent_url}/present-proof/send-request",
            json=RequestPresentationV1(
                comment="Performance Verification",
                connection_id=connection_id,
                proof_request=self.proof_request,
            ).model_dump(),
            headers=self.headers,
        )

        try:
            if r.status_code != 200:
                raise Exception("Request was not successful: ", r.content)
            presentation_request = r.json()
        except JSONDecodeError:
            raise Exception(
                "Encountered JSONDecodeError while parsing the request: ", r.text
            )

        return presentation_request["presentation_exchange_id"]

    def verify_verification(self, presentation_exchange_id):
        iteration = 0
        try:
            while iteration < self.verifiedTimeoutSeconds:
                r = requests.get(
                    f"{self.agent_url}/present-proof/records/{presentation_exchange_id}",
                    headers=self.headers,
                )
                if r.status_code != 200:
                    raise Exception(
                        f"Failed to get presentation record: status {r.status_code}, body: {r.text}"
                    )
                presentation_record = r.json()
                presentation_state = presentation_record["state"]
                if (
                    presentation_state != "request_sent"
                    and presentation_state != "presentation_received"
                ):
                    break
                iteration += 1
                time.sleep(1)

            if iteration >= self.verifiedTimeoutSeconds:
                raise TimeoutError(
                    f"Presentation verification timed out after {self.verifiedTimeoutSeconds}s, "
                    f"last state: '{presentation_state}'"
                )

            if presentation_record["verified"] is not True:
                raise AssertionError(
                    f"Presentation was not successfully verified. Presentation in state {presentation_state}"
                )

        except JSONDecodeError as e:
            raise Exception(
                f"Encountered JSONDecodeError while getting the presentation record: {e}. Response text: {r.text if 'r' in locals() else 'N/A'}"
            )

        return True
