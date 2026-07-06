import re
import time

import requests
from models import (
    AnonCredsRevocation,
    CredentialProposalV1 as CredentialProposal,
    IssueCredentialV1 as IssueCredential,
)
from settings import Settings

from .base import BaseIssuer
from ..base_acapy import BaseAcapyAgent


def _strip_did_prefix(did: str) -> str:
    """Strip did:method: prefix from a DID string."""
    return re.sub(r"^did:\w+:", "", did) if did else did


class AcapyIssuer(BaseIssuer, BaseAcapyAgent):
    def __init__(self):
        super().__init__()
        if Settings.IS_ANONCREDS:
            self.revoke_endpoint = "/anoncreds/revocation/revoke"
        else:
            self.revoke_endpoint = "/revocation/revoke"
        self._ensure_cred_def_operable()

    def _ensure_cred_def_operable(self):
        if not self.cred_def_id:
            return

        self.cred_def_id = _strip_did_prefix(self.cred_def_id)

        if Settings.IS_ANONCREDS:
            r = requests.get(
                f"{self.agent_url}/anoncreds/credential-definitions",
                headers=self.headers,
                params={
                    "schema_id": self.schema_id,
                },
            )
        else:
            r = requests.get(
                f"{self.agent_url}/credential-definitions/created",
                headers=self.headers,
                params={"cred_def_id": self.cred_def_id},
            )
        if r.status_code != 200:
            raise Exception(
                f"Failed to check credential definitions: {r.content}"
            )

        cred_def_ids = r.json().get("credential_definition_ids", [])

        if self.cred_def_id in cred_def_ids:
            return

        tag = (
            self.cred_def_id.rsplit(":", 1)[-1]
            if ":" in self.cred_def_id
            else "default"
        )

        if Settings.IS_ANONCREDS:
            r = requests.post(
                f"{self.agent_url}/anoncreds/credential-definition",
                headers=self.headers,
                json={
                    "credential_definition": {
                        "issuerId": self.cred_def_id.split(":")[0],
                        "schemaId": self.schema_id,
                        "tag": tag,
                    },
                    "options": {},
                },
            )
        else:
            r = requests.post(
                f"{self.agent_url}/credential-definitions",
                headers=self.headers,
                json={
                    "schema_id": self.schema_id,
                    "tag": tag,
                    "support_revocation": False,
                },
            )
        if r.status_code != 200:
            raise Exception(
                f"Failed to create credential definition: {r.content}"
            )

        new_cred_def_id = r.json().get("credential_definition_id", "")
        if not new_cred_def_id:
            raise Exception("No credential_definition_id in response")

        self.cred_def_id = new_cred_def_id
        Settings.CRED_DEF_ID = new_cred_def_id

    def issue_credential(self, connection_id):
        r = requests.post(
            f"{self.agent_url}/issue-credential/send",
            headers=self.headers,
            json=IssueCredential(
                auto_remove=True,
                connection_id=connection_id,
                cred_def_id=self.cred_def_id,
                credential_proposal=CredentialProposal(
                    attributes=self.cred_attributes
                ),
                trace=True,
            ).model_dump(),
        )
        if r.status_code != 200:
            raise Exception(r.content)

        cred_ex = r.json()

        return {
            "connection_id": cred_ex["connection_id"],
            "cred_ex_id": cred_ex["credential_exchange_id"],
        }

    def revoke_credential(self, connection_id, credential_exchange_id):
        time.sleep(1)
        payload = AnonCredsRevocation(
            comment="Load Test",
            connection_id=connection_id,
            cred_ex_id=credential_exchange_id,
            notify_version="v1_0",
        ).model_dump()
        r = requests.post(
            f"{self.agent_url}{self.revoke_endpoint}",
            json=payload,
            headers=self.headers,
        )
        if r.status_code != 200:
            raise Exception(r.content)
