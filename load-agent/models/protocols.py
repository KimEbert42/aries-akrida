from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class BaseModel(BaseModel):
    def model_dump(self, **kwargs) -> Dict[str, Any]:
        return super().model_dump(by_alias=True, exclude_none=True, **kwargs)


class CredentialProposal(BaseModel):
    type: str = Field('issue-credential/1.0/credential-preview', alias='@type')
    attributes: list = Field()


class IssueCredential(BaseModel):
    auto_remove: bool = Field(True)
    comment: Optional[str] = Field(default=None)
    connection_id: str = Field()
    cred_def_id: str = Field()
    credential_proposal: CredentialProposal = Field()
    issuer_did: Optional[str] = Field(default=None)
    schema_id: Optional[str] = Field(default=None)
    schema_issuer_did: Optional[str] = Field(default=None)
    schema_name: Optional[str] = Field(default=None)
    schema_version: Optional[str] = Field(default=None)
    trace: bool = Field(True)


class ProofRequest(BaseModel):
    name: str = Field()
    requested_attributes: dict = Field()
    requested_predicates: dict = Field()
    version: str = Field()


class RequestPresentation(BaseModel):
    auto_remove: bool = Field(False)
    auto_verify: bool = Field(True)
    connection_id: str = Field(None)
    comment: str = Field()
    proof_request: ProofRequest = Field()
    trace: bool = Field(True)


class AnonCredsRevocation(BaseModel):
    comment: Optional[str] = Field(default=None)
    connection_id: str = Field()
    cred_ex_id: str = Field()
    notify: bool = Field(True)
    notify_version: str = Field()
    publish: bool = Field(True)