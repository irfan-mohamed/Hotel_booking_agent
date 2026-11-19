import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Import the FastAPI app – adjust the import path according to your project layout
from app.main import app

client = TestClient(app)

@pytest.fixture
def email():
    """A deterministic email address used across tests."""
    return "test_user@example.com"

def _extract_token_from_mock_call(mock_send):
    """
    Helper that extracts the verification token that the mocked email‑sending
    function was called with.  The real implementation of ``send_verification_email``
    is expected to receive ``email`` and ``token`` as positional arguments.
    """
    assert mock_send.called, "Email sending function was not called"
    # The first call args: (email, token, ...) – token is the second positional arg
    _, token, *_ = mock_send.call_args[0]
    return token

def test_token_is_generated_and_email_sent(email):
    """
    Ensure that requesting a verification email generates a token and that the
    email‑sending routine is invoked with that token.
    """
    with patch("app.email.send_verification_email") as mock_send:
        response = client.post(
            "/api/v1/auth/request-verification",
            json={"email": email},
        )
        assert response.status_code == 200
        # The endpoint may return a generic success message; we only care that
        # the email function was called.
        token = _extract_token_from_mock_call(mock_send)
        assert isinstance(token, str) and len(token) > 0

def test_successful_email_verification_flow(email):
    """
    End‑to‑end test: request a verification token, then verify it and assert that
    the user becomes verified.
    """
    with patch("app.email.send_verification_email") as mock_send:
        # Step 1 – request verification, which triggers token generation
        resp_req = client.post(
            "/api/v1/auth/request-verification",
            json={"email": email},
        )
        assert resp_req.status_code == 200
        token = _extract_token_from_mock_call(mock_send)

    # Step 2 – hit the verification endpoint with the valid token
    resp_verify = client.get(f"/api/v1/auth/verify-email?token={token}")
    assert resp_verify.status_code == 200
    assert resp_verify.json().get("detail") == "Email verified successfully"

    # Step 3 – confirm the user record reflects the verified state.
    # The project is expected to expose an endpoint that returns user status.
    resp_status = client.get(f"/api/v1/users/status?email={email}")
    assert resp_status.status_code == 200
    data = resp_status.json()
    assert data.get("is_verified") is True

def test_verification_with_invalid_or_expired_token(email):
    """
    Verify that providing an invalid or expired token yields an appropriate
    error response and does not mark the user as verified.
    """
    # Use a clearly bogus token
    bogus_token = "this-token-does-not-exist-or-is-expired"
    resp = client.get(f"/api/v1/auth/verify-email?token={bogus_token}")
    # The exact status code depends on implementation – 400/401/422 are common.
    assert resp.status_code in (400, 401, 422)
    json_resp = resp.json()
    # The error payload should contain a message indicating the problem.
    assert "invalid" in json_resp.get("detail", "").lower() or "expired" in json_resp.get("detail", "").lower()

    # Ensure the user is still unverified (if the user exists)
    resp_status = client.get(f"/api/v1/users/status?email={email}")
    if resp_status.status_code == 200:
        assert resp_status.json().get("is_verified") is False