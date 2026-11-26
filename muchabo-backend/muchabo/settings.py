"""Validated, secret-aware runtime configuration loaded at startup."""

from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, ValidationError, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """External service destinations and credentials; no bot behavior lives here."""

    model_config = SettingsConfigDict(env_prefix="MUCHABO_", env_file=".env", extra="ignore", hide_input_in_errors=True)

    app_name: str = "muchabo backend"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    admin_base_url: SecretStr
    admin_access_token: SecretStr
    litellm_base_url: SecretStr
    litellm_api_key: SecretStr
    langfuse_base_url: SecretStr = Field(validation_alias="LANGFUSE_BASE_URL")
    langfuse_public_key: SecretStr = Field(validation_alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: SecretStr = Field(validation_alias="LANGFUSE_SECRET_KEY")
    observe_io_capture: bool = Field(validation_alias="LANGFUSE_OBSERVE_DECORATOR_IO_CAPTURE_ENABLED")
    media_upload: bool = Field(validation_alias="LANGFUSE_MEDIA_UPLOAD_ENABLED")

    @field_validator("admin_base_url", "litellm_base_url", "langfuse_base_url")
    @classmethod
    def validate_destination(cls, value: SecretStr, info: ValidationInfo) -> SecretStr:
        """Require HTTPS, permitting loopback HTTP solely for local validation."""
        try:
            raw = value.get_secret_value()
            url = urlsplit(raw)
            valid = (
                bool(url.hostname)
                and url.port != 0
                and not url.username
                and not url.password
                and not url.query
                and not url.fragment
                and not any(char.isspace() for char in raw)
                and (url.scheme == "https" or (url.scheme == "http" and url.hostname in {"localhost", "127.0.0.1", "::1"}))
            )
            if info.field_name == "admin_base_url":
                valid = valid and url.path in {"", "/"}
            if not valid:
                raise ValueError
        except ValueError:
            raise ValueError("Invalid service destination") from None
        return value

    @field_validator("admin_access_token", "litellm_api_key", "langfuse_public_key", "langfuse_secret_key")
    @classmethod
    def validate_credential(cls, value: SecretStr) -> SecretStr:
        """Reject blank credentials and header control characters."""
        raw = value.get_secret_value()
        if not raw.strip() or any(char.isspace() for char in raw):
            raise ValueError("Invalid service credential")
        return value

    @field_validator("observe_io_capture", "media_upload")
    @classmethod
    def require_content_disabled(cls, value: bool) -> bool:
        """Content capture and media uploads must be explicitly disabled."""
        if value:
            raise ValueError("Content capture must be disabled")
        return value


def load_settings() -> Settings:
    """Load settings with a startup error containing field names only."""
    try:
        return Settings()
    except ValidationError as error:
        fields = sorted({str(item["loc"][0]) for item in error.errors(include_input=False, include_context=False)})
        raise ValueError("Missing or invalid runtime settings: " + ", ".join(fields)) from None
