from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ASSESSMENT_NUMBER = "+18054398008"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_from_number: str
    public_base_url: str
    test_phone_number: str = ASSESSMENT_NUMBER
    openai_realtime_model: str = "gpt-realtime-1.5"
    openai_analysis_model: str = "gpt-5-mini"
    openai_voice: str = "marin"
    artifact_dir: Path = Field(default=Path("artifacts"))

    @field_validator("test_phone_number")
    @classmethod
    def enforce_assessment_number(cls, value: str) -> str:
        if value != ASSESSMENT_NUMBER:
            raise ValueError(f"destination is locked to {ASSESSMENT_NUMBER}")
        return value

    @field_validator("public_base_url")
    @classmethod
    def validate_public_url(cls, value: str) -> str:
        value = value.rstrip("/")
        parsed = urlparse(value)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("PUBLIC_BASE_URL must be a public HTTPS URL")
        return value

    @property
    def public_ws_url(self) -> str:
        return "wss://" + self.public_base_url.removeprefix("https://")

