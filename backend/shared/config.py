from pydantic_settings import BaseSettings
from pydantic import Field
from urllib.parse import urlparse


class Settings(BaseSettings):
    # Supabase
    supabase_url: str = Field(..., env="SUPABASE_URL")
    supabase_service_key: str = Field(..., env="SUPABASE_SERVICE_KEY")
    supabase_jwt_secret: str = Field(..., env="SUPABASE_JWT_SECRET")

    # Optional override for the SQLAlchemy connection URL.
    # Recommended: the Supabase pooler connection string, e.g.
    # postgresql://postgres.<ref>:<password>@aws-1-ap-south-1.pooler.supabase.com:6543/postgres
    database_url: str | None = Field(None, env="DATABASE_URL")

    # App
    environment: str = Field("production", env="ENVIRONMENT")
    service_name: str = Field("unknown", env="SERVICE_NAME")

    @property
    def db_url(self) -> str:
        """SQLAlchemy connection URL used by all services.

        Prefers DATABASE_URL when set. Otherwise falls back to deriving the
        host from the Supabase project URL.
        """
        if self.database_url:
            return self.database_url
        parsed = urlparse(self.supabase_url)
        project_ref = parsed.hostname.split('.')[0]
        host = f"db.{project_ref}.supabase.co"
        # The DB password is the same as the service role key for Supabase
        return (
            f"postgresql+psycopg2://postgres:{self.supabase_service_key}"
            f"@{host}:5432/postgres"
        )

    @property
    def supabase_anon_key(self) -> str:
        """The anon key can be derived or set separately."""
        return self.supabase_service_key

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
