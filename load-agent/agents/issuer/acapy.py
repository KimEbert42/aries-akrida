import time

import requests
from models import AnonCredsRevocation, CredentialProposalV1, IssueCredentialV1

from .base import BaseIssuer
from ..base_acapy import BaseAcapyAgent


class AcapyIssuer(BaseIssuer, BaseAcapyAgent):
    def issue_credential(self, connection_id):
        schema_issuer_did, schema_rest = self.schema_id.split(":2:", 1)
        schema_name, schema_version = schema_rest.split(":", 1)
        issuer_did = self.cred_def_id.split(":3:CL:")[0]

        payload = IssueCredentialV1(
            connection_id=connection_id,
            comment="Performance Issuance",
            cred_def_id=self.cred_def_id,
            issuer_did=issuer_did,
            schema_id=self.schema_id,
            schema_issuer_did=schema_issuer_did,
            schema_name=schema_name,
            schema_version=schema_version,
            credential_proposal=CredentialProposalV1(attributes=self.cred_attributes),
        ).model_dump()

        r = requests.post(
            f"{self.agent_url}/issue-credential/send",
            json=payload,
            headers=self.headers,
        )
        if r.status_code != 200:
            raise Exception(r.content)

        cred_offer = r.json()

        return {
            "connection_id": cred_offer["connection_id"],
            "cred_ex_id": cred_offer["credential_exchange_id"],
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
            f"{self.agent_url}/revocation/revoke",
            json=payload,
            headers=self.headers,
        )
        if r.status_code != 200:
            raise Exception(r.content)
