import pytest
from pydantic import ValidationError

from voice_tester.config import ASSESSMENT_NUMBER, Settings


BASE = {
    "openai_api_key": "test",
    "twilio_account_sid": "ACtest",
    "twilio_auth_token": "test",
    "twilio_from_number": "+15551234567",
    "public_base_url": "https://example.test",
}


def test_destination_is_locked() -> None:
    settings = Settings(**BASE)
    assert settings.test_phone_number == ASSESSMENT_NUMBER
    with pytest.raises(ValidationError):
        Settings(**BASE, test_phone_number="+15550000000")


def test_public_url_requires_https() -> None:
    with pytest.raises(ValidationError):
        Settings(**{**BASE, "public_base_url": "http://localhost:8000"})

