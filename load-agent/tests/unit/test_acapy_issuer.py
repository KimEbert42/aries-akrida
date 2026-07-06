import os

os.environ["ISSUER_URL"] = "http://localhost:8150"
os.environ["ISSUER_HEADERS"] = '{"X-API-Key": "test-api-key"}'
os.environ["VERIFIER_URL"] = ""
os.environ["VERIFIER_HEADERS"] = "{}"
os.environ["HOLDER_URL"] = ""
os.environ["START_PORT"] = "8150"
os.environ["END_PORT"] = "9150"
os.environ["SCHEMA"] = "did:indy:test:123456789abcdef:2:TestSchema:1.0"
os.environ["CRED_DEF"] = "did:indy:test:123456789abcdef:3:CL:1234:default"
os.environ["CRED_ATTR"] = (
    '[{"name": "attr1", "value": "test"}, {"name": "attr2", "value": "test2"}]'
)

import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


class TestAcapyIssuerUnit:
    @pytest.fixture(autouse=True)
    def setup_issuer(self):
        from agents.issuer.acapy import AcapyIssuer

        with patch.object(AcapyIssuer, "_ensure_cred_def_operable"):
            self.issuer = AcapyIssuer()
        self.issuer.agent_url = "http://localhost:8150"
        self.issuer.headers = {
            "X-API-Key": "test-api-key",
            "Content-Type": "application/json",
        }

    def test_issuer_has_correct_base_url(self):
        assert self.issuer.agent_url == "http://localhost:8150"

    def test_issuer_has_correct_headers(self):
        assert self.issuer.headers["X-API-Key"] == "test-api-key"
        assert self.issuer.headers["Content-Type"] == "application/json"

    def test_issuer_has_schema_and_cred_def_ids(self):
        assert self.issuer.schema_id == os.environ["SCHEMA"]
        assert self.issuer.cred_def_id == os.environ["CRED_DEF"]

    def test_issue_credential_returns_correct_structure(self):
        with patch("agents.issuer.acapy.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "connection_id": "test-connection-id",
                "credential_exchange_id": "test-cred-ex-id",
            }
            mock_post.return_value = mock_response

            result = self.issuer.issue_credential("test-connection-id")

            assert result["connection_id"] == "test-connection-id"
            assert result["cred_ex_id"] == "test-cred-ex-id"
            mock_post.assert_called_once()

            call_args = mock_post.call_args
            assert "/issue-credential/send" in call_args[0][0]
            assert call_args[1]["headers"] == self.issuer.headers

    def test_issue_credential_uses_v1_payload(self):
        with patch("agents.issuer.acapy.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "connection_id": "test-connection-id",
                "credential_exchange_id": "test-cred-ex-id",
            }
            mock_post.return_value = mock_response

            self.issuer.issue_credential("test-connection-id")

            call_args = mock_post.call_args
            payload = call_args[1]["json"]

            assert payload["connection_id"] == "test-connection-id"
            assert payload["cred_def_id"] == self.issuer.cred_def_id
            assert "credential_proposal" in payload
            assert payload["credential_proposal"]["@type"] == (
                "issue-credential/1.0/credential-preview"
            )
            assert len(payload["credential_proposal"]["attributes"]) == 2

    def test_issue_credential_raises_on_non_200(self):
        with patch("agents.issuer.acapy.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.content = b"Internal Server Error"
            mock_post.return_value = mock_response

            with pytest.raises(Exception, match="Internal Server Error"):
                self.issuer.issue_credential("test-connection-id")

    def test_revoke_credential_calls_correct_endpoint(self):
        with patch("agents.issuer.acapy.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            self.issuer.revoke_credential(
                "test-connection-id", "test-cred-ex-id"
            )

            call_args = mock_post.call_args
            assert "/revocation/revoke" in call_args[0][0]

            payload = call_args[1]["json"]
            assert payload["connection_id"] == "test-connection-id"
            assert payload["cred_ex_id"] == "test-cred-ex-id"
            assert payload["notify_version"] == "v1_0"

    def test_revoke_credential_raises_on_non_200(self):
        with patch("agents.issuer.acapy.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.content = b"Revocation Failed"
            mock_post.return_value = mock_response

            with pytest.raises(Exception, match="Revocation Failed"):
                self.issuer.revoke_credential(
                    "test-connection-id", "test-cred-ex-id"
                )

    def test_ensure_cred_def_operable_creates_if_missing(self):
        from agents.issuer.acapy import AcapyIssuer, Settings

        with patch.object(AcapyIssuer, "_ensure_cred_def_operable"):
            issuer = AcapyIssuer()

        issuer.agent_url = "http://localhost:8150"
        issuer.headers = {
            "X-API-Key": "test-api-key",
            "Content-Type": "application/json",
        }
        issuer.cred_def_id = "did:indy:test:missing:3:CL:9999:default"
        issuer.schema_id = "did:indy:test:missing:2:TestSchema:1.0"

        with patch(
            "agents.issuer.acapy.requests.get"
        ) as mock_get, patch(
            "agents.issuer.acapy.requests.post"
        ) as mock_post:
            mock_get_response = MagicMock()
            mock_get_response.status_code = 200
            mock_get_response.json.return_value = {
                "credential_definition_ids": []
            }
            mock_get.return_value = mock_get_response

            mock_post_response = MagicMock()
            mock_post_response.status_code = 200
            mock_post_response.json.return_value = {
                "credential_definition_id": "did:indy:test:new:3:CL:9999:default"
            }
            mock_post.return_value = mock_post_response

            issuer._ensure_cred_def_operable()

            mock_post.assert_called_once()
            payload = mock_post.call_args[1]["json"]
            assert payload["schema_id"] == issuer.schema_id
            assert payload["tag"] == "default"
            assert issuer.cred_def_id == "did:indy:test:new:3:CL:9999:default"
            assert Settings.CRED_DEF_ID == "did:indy:test:new:3:CL:9999:default"

    def test_ensure_cred_def_operable_skips_if_exists(self):
        from agents.issuer.acapy import AcapyIssuer

        with patch.object(AcapyIssuer, "_ensure_cred_def_operable"):
            issuer = AcapyIssuer()

        issuer.agent_url = "http://localhost:8150"
        issuer.headers = {
            "X-API-Key": "test-api-key",
            "Content-Type": "application/json",
        }

        with patch(
            "agents.issuer.acapy.requests.get"
        ) as mock_get:
            mock_get_response = MagicMock()
            mock_get_response.status_code = 200
            mock_get_response.json.return_value = {
                "credential_definition_ids": [issuer.cred_def_id]
            }
            mock_get.return_value = mock_get_response

            issuer._ensure_cred_def_operable()

            mock_get.assert_called_once()


class TestAcapyIssuerBaseMethods:
    @pytest.fixture(autouse=True)
    def setup_issuer(self):
        from agents.issuer.acapy import AcapyIssuer

        with patch.object(AcapyIssuer, "_ensure_cred_def_operable"):
            self.issuer = AcapyIssuer()
        self.issuer.agent_url = "http://localhost:8150"
        self.issuer.headers = {
            "X-API-Key": "test-api-key",
            "Content-Type": "application/json",
        }

    def test_is_up_returns_true_when_healthy(self):
        with patch("agents.issuer.acapy.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            assert self.issuer.is_up() is True

    def test_is_up_returns_false_on_error(self):
        with patch("agents.issuer.acapy.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.content = b"Error"
            mock_get.return_value = mock_response

            assert self.issuer.is_up() is False

    def test_is_up_returns_false_on_exception(self):
        with patch("agents.issuer.acapy.requests.get") as mock_get:
            mock_get.side_effect = Exception("Connection refused")

            assert self.issuer.is_up() is False

    def test_get_invite_returns_connection_id(self):
        with patch("agents.issuer.acapy.requests.post") as mock_post, \
             patch("agents.issuer.acapy.requests.get") as mock_get:
            mock_invitation_response = MagicMock()
            mock_invitation_response.json.return_value = {
                "invi_msg_id": "test-msg-id",
                "invitation_url": "http://example.com/invite",
            }
            mock_post.return_value = mock_invitation_response

            mock_conn_response = MagicMock()
            mock_conn_response.json.return_value = {
                "results": [{"connection_id": "test-conn-id"}]
            }
            mock_get.return_value = mock_conn_response

            result = self.issuer.get_invite()

            assert result["connection_id"] == "test-conn-id"
            assert result["invitation_url"] == "http://example.com/invite"
