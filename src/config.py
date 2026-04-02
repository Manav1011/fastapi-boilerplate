from enum import Enum
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings

load_dotenv(override=True)


class AppEnvironment(str, Enum):
    """
    Enum representing different application environments.

    - LOCAL: Indicates that the application is running on a local machine or environment.
    - DEVELOPMENT: Indicates that the application is running in a development environment.
    - PRODUCTION: Indicates that the application is running in a production environment.
    """

    LOCAL = "Local"
    DEVELOPMENT = "Development"
    PRODUCTION = "Production"


class Settings(BaseSettings):
    """
    A settings class for the project defining all the necessary parameters within the
    app through an object.
    """

    # App variables
    ENV: Optional[AppEnvironment] = Field(None, alias="ENV")
    APP_NAME: Optional[str] = Field(None, alias="APP_NAME")
    APP_VERSION: Optional[str] = Field(None, alias="APP_VERSION")
    APP_HOST: Optional[str] = Field(None, alias="APP_HOST")
    APP_PORT: Optional[int] = Field(None, alias="APP_PORT")
    APP_DEBUG: Optional[bool] = Field(False, alias="APP_DEBUG")
    APP_CONTAINER: Optional[bool] = Field(False, alias="APP_CONTAINER")

    # JWT Token variables
    JWT_SECRET_KEY: Optional[str] = Field(None, alias="JWT_SECRET_KEY")
    JWT_ALGORITHM: Optional[str] = Field(None, alias="JWT_ALGORITHM")
    COOKIES_DOMAIN: Optional[str] = Field(None, alias="COOKIES_DOMAIN")
    ACCESS_TOKEN_EXP: Optional[int] = Field(3600, alias="ACCESS_TOKEN_EXP")
    REFRESH_TOKEN_EXP: Optional[int] = Field(86400, alias="REFRESH_TOKEN_EXP")

    DATABASE_USER: Optional[str] = Field(None, alias="DATABASE_USER")
    DATABASE_PASSWORD: Optional[str] = Field(None, alias="DATABASE_PASSWORD")
    DATABASE_HOST: Optional[str] = Field(None, alias="DATABASE_HOST")
    DATABASE_PORT: Optional[str] = Field(None, alias="DATABASE_PORT")
    DATABASE_NAME: Optional[str] = Field(None, alias="DATABASE_NAME")
    DATABASE_URL: Optional[str] = Field(None, alias="DATABASE_URL")

    MASTER_ENUM_FILE_PATH: Optional[str] = Field(None, alias="MASTER_ENUM_FILE_PATH")

    REDIS_URL: Optional[str] = Field(None, alias="REDIS_URL")

    # Sentry variables
    SENTRY_SDK_DSN: str | None = Field(None, alias="SENTRY_SDK_DSN")

    model_config = {"env_file": ".env", "extra": "ignore"}

    # Add a root validator for required fields
    @model_validator(mode="after")
    def validate_required(self):
        """
        Validate the required fields for the application.
        """
        required_fields = [
            "ENV",
            "JWT_SECRET_KEY",
            "JWT_ALGORITHM",
            "DATABASE_USER",
            "DATABASE_PASSWORD",
            "DATABASE_HOST",
            "DATABASE_PORT",
            "DATABASE_NAME",
            "SENTRY_SDK_DSN",
        ]
        missing = [field for field in required_fields if not getattr(self, field)]
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )
        return self

    @field_validator("DATABASE_URL", mode="before")
    def assemble_db_url(cls, val, values) -> str:
        """
        Create a Database URL from the settings provided in the .env file.
        """
        if isinstance(val, str) and val:
            return val

        database_user = values.data.get("DATABASE_USER")
        database_password = values.data.get("DATABASE_PASSWORD")
        database_host = values.data.get("DATABASE_HOST")
        database_port = values.data.get("DATABASE_PORT")
        if database_port:
            database_port = str(database_port).replace('"', "")
        database_name = values.data.get("DATABASE_NAME")

        if not all(
            [
                database_user,
                database_password,
                database_host,
                database_port,
                database_name,
            ]
        ):
            raise ValueError("Incomplete database connection information")

        return (
            f"postgresql+asyncpg://"
            f"{database_user}:{database_password}@{database_host}:{database_port}/{database_name}"
        )

    @property
    def is_production(self) -> bool:
        """
        Check if the app is running in production mode.
        """
        return self.ENV == AppEnvironment.PRODUCTION

    @property
    def is_development(self) -> bool:
        """
        Check if the app is running in development mode.
        """
        return self.ENV == AppEnvironment.DEVELOPMENT

    @property
    def is_local(self) -> bool:
        """
        Check if the app is running in local mode.
        """
        return self.ENV == AppEnvironment.LOCAL


settings = Settings()
