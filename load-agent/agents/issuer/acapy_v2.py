import time

import requests
from models import (
    AnonCredsFilter,
    AnonCredsRevocation,
    CredentialPreview,
    Filter,
    IndyFilter,
)
from models import (
    IssueCredentialV2 as IssueCredential,
)
from settings import Settings

from .base import BaseIssuer
from ..base_acapy import BaseAcapyAgent


class AcapyIssuer(BaseIssuer, BaseAcapyAgent):
    def __init__(self):
        super().__init__()
        schema_issuer_id, schema_rest = self.schema_id.split(":2:", 1)
        schema_name, schema_version = schema_rest.split(":", 1)
        issuer_id = self.cred_def_id.split(":3:CL:")[0]
        filter_kwargs = dict(
            cred_def_id=self.cred_def_id,
            schema_id=self.schema_id,
            schema_issuer_id=schema_issuer_id,
            schema_name=schema_name,
            schema_version=schema_version,
            issuer_id=issuer_id,
        )
        if Settings.IS_ANONCREDS:
            self.filter = AnonCredsFilter(anoncreds=Filter(**filter_kwargs))
            self.revoke_endpoint = "/anoncreds/revocation/revoke"
        else:
            self.revoke_endpoint = "/revocation/revoke"
            self.filter = IndyFilter(indy=Filter(**filter_kwargs))

    def issue_credential(self, connection_id):
                
        r = requests.post(
            f"{self.agent_url}/issue-credential-2.0/send",
            headers=self.headers,
            json=IssueCredential(
                auto_issue=True,
                connection_id=connection_id,
                credential_preview=CredentialPreview(attributes=self.cred_attributes),
                filter=self.filter,
            ).model_dump(),
        )
        if r.status_code != 200:
            raise Exception(r.content)

        cred_ex = r.json()

        return {
            "connection_id": cred_ex["connection_id"],
            "cred_ex_id": cred_ex["cred_ex_id"],
        }

    def revoke_credential(self, connection_id, cred_ex_id):
        time.sleep(1)
        r = requests.post(
            f"{self.agent_url}{self.revoke_endpoint}",
            headers=self.headers,
            json=AnonCredsRevocation(
                connection_id=connection_id,
                cred_ex_id=cred_ex_id,
                notify_version="v1_0",
            ).model_dump(),
        )
        if r.status_code != 200:
            raise Exception(r.content)
