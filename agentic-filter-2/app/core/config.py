from functools import lru_cache
from typing import Literal
from urllib.parse import quote_plus

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    database_url: str = Field(
        default="postgresql+psycopg://user:pass@127.0.0.1:5432/filter_db",
        validation_alias="DATABASE_URL",
    )
    runtime_postgres_url: str | None = Field(
        default=None,
        validation_alias="RUNTIME_POSTGRES_URL",
        description="URL for executing filtered runtime SQL; defaults to DATABASE_URL when unset.",
    )
    runtime_query_timeout_seconds: float = Field(
        default=30.0,
        ge=1.0,
        le=120.0,
        validation_alias="RUNTIME_QUERY_TIMEOUT_SECONDS",
    )
    opensearch_base_url: str | None = Field(
        default=None,
        validation_alias="OPENSEARCH_BASE_URL",
        description=(
            "Full OpenSearch HTTP base URL. When set, overrides OPENSEARCH_HOST/PORT."
        ),
    )
    opensearch_host: str | None = Field(
        default=None,
        validation_alias="OPENSEARCH_HOST",
        description="OpenSearch host (used with OPENSEARCH_PORT when BASE_URL unset).",
    )
    opensearch_port: int = Field(
        default=9200,
        ge=1,
        le=65535,
        validation_alias="OPENSEARCH_PORT",
    )
    opensearch_user: str | None = Field(
        default=None,
        validation_alias="OPENSEARCH_USER",
    )
    opensearch_password: str | None = Field(
        default=None,
        validation_alias="OPENSEARCH_PASSWORD",
    )
    opensearch_index: str = Field(
        default="data_dictionary",
        validation_alias=AliasChoices("OPENSEARCH_INDEX", "METADATA_OPENSEARCH_INDEX"),
        description="Default index for metadata dictionary API.",
    )
    opensearch_use_ssl: bool = Field(
        default=False,
        validation_alias="OPENSEARCH_USE_SSL",
        description="Use https:// when building URL from OPENSEARCH_HOST/PORT.",
    )
    opensearch_verify_certs: bool = Field(
        default=True,
        validation_alias="OPENSEARCH_VERIFY_CERTS",
        description="TLS certificate verification (set false for self-signed dev clusters).",
    )
    opensearch_timeout_seconds: float = Field(
        default=30.0,
        ge=1.0,
        le=120.0,
        validation_alias="OPENSEARCH_TIMEOUT_SECONDS",
    )
    metadata_hybrid_enabled: bool = Field(
        default=True,
        validation_alias="METADATA_HYBRID_ENABLED",
        description="When false, hybrid-search uses keyword-only bool query.",
    )
    metadata_embedding_model: str = Field(
        default="BAAI/bge-m3",
        validation_alias=AliasChoices(
            "METADATA_EMBEDDING_MODEL", "EMBEDDING_MODEL"
        ),
        description="SentenceTransformer model for hybrid kNN (agentic-agri default).",
    )
    metadata_embedding_dim: int = Field(
        default=1024,
        ge=1,
        validation_alias=AliasChoices("METADATA_EMBEDDING_DIM", "EMBEDDING_DIM"),
        description="Vector dimension for description_vector (bge-m3 = 1024).",
    )
    masking_hash_salt: str = Field(
        default="dev-masking-salt-change-in-prod",
        min_length=8,
        max_length=256,
        validation_alias="MASKING_HASH_SALT",
        description="Salt for HASH mask type (§3.7).",
    )
    redis_url: str = Field(
        default="redis://127.0.0.1:6379/0",
        validation_alias="REDIS_URL",
    )
    iam_base_url: str = Field(
        default="https://iam.example.com",
        validation_alias="IAM_BASE_URL",
    )
    iam_token_validate_path: str = Field(
        default="/v1/token/validate",
        validation_alias="IAM_TOKEN_VALIDATE_PATH",
    )
    iam_timeout_seconds: float = Field(
        default=2.5,
        ge=0.5,
        le=30.0,
        validation_alias="IAM_TIMEOUT_SECONDS",
    )
    iam_max_retries: int = Field(
        default=2,
        ge=0,
        le=5,
        validation_alias="IAM_MAX_RETRIES",
    )
    iam_circuit_breaker_enabled: bool = Field(
        default=False,
        validation_alias="IAM_CIRCUIT_BREAKER_ENABLED",
    )
    user_context_ttl_seconds: int = Field(
        default=600,
        ge=60,
        le=900,
        description="TTL for user_context:{user_id} cache (architecture §3.3: 5–15 min).",
        validation_alias="USER_CONTEXT_TTL_SECONDS",
    )
    permission_snapshot_ttl_seconds: int = Field(
        default=180,
        ge=30,
        le=600,
        description="TTL for permission_snapshot:{user_id} (architecture §3.3: 1–5 min).",
        validation_alias="PERMISSION_SNAPSHOT_TTL_SECONDS",
    )
    user_context_cache_backend: Literal["redis", "memory"] = Field(
        default="redis",
        validation_alias="USER_CONTEXT_CACHE_BACKEND",
    )
    admin_api_token: str | None = Field(
        default=None,
        validation_alias="ADMIN_API_TOKEN",
        description="If set, require matching X-Admin-Token on admin routes (MVP guard).",
    )
    auth_bypass_enabled: bool = Field(
        default=False,
        validation_alias="AUTH_BYPASS_ENABLED",
        description=(
            "Local/dev only: skip IAM token validation on runtime/filter routes. "
            "Any non-empty Bearer token is accepted; user is taken from AUTH_BYPASS_*."
        ),
    )
    auth_bypass_user_id: str = Field(
        default="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        validation_alias="AUTH_BYPASS_USER_ID",
        description="User id when AUTH_BYPASS_ENABLED (must exist in Permission DB; demo seed default).",
    )
    auth_bypass_username: str = Field(
        default="demo_user",
        validation_alias="AUTH_BYPASS_USERNAME",
    )
    auth_bypass_email: str = Field(
        default="demo@local.dev",
        validation_alias="AUTH_BYPASS_EMAIL",
    )
    cors_allowed_origins: str = Field(
        default=(
            "http://localhost:3000,http://127.0.0.1:3000,"
            "http://localhost:5173,http://127.0.0.1:5173,"
            "http://localhost:4200,http://127.0.0.1:4200"
        ),
        validation_alias="CORS_ALLOWED_ORIGINS",
        description="Comma-separated origins for browser FE (CORS). Use * only without credentials.",
    )

    sql_catalog_database_name: str = Field(
        default="COREDB",
        validation_alias="SQL_CATALOG_DATABASE_NAME",
        description="Logical database name in permission catalog for /api/v1/sql/*.",
    )
    pg_host: str = Field(default="localhost", validation_alias="PG_HOST")
    pg_port: int = Field(
        default=5432,
        ge=1,
        le=65535,
        validation_alias="PG_PORT",
    )
    pg_user: str | None = Field(default=None, validation_alias="PG_USER")
    pg_password: str | None = Field(default=None, validation_alias="PG_PASSWORD")
    pg_database: str | None = Field(default=None, validation_alias="PG_DATABASE")

    @property
    def effective_runtime_postgres_url(self) -> str:
        """URL for runtime SELECT execution (/filter, /sql/execute).

        Priority: RUNTIME_POSTGRES_URL → PG_* components → DATABASE_URL.
        Permission catalog always uses DATABASE_URL.
        """
        explicit = (self.runtime_postgres_url or "").strip()
        if explicit:
            return explicit
        db = (self.pg_database or "").strip()
        user = (self.pg_user or "").strip()
        if db and user:
            host = (self.pg_host or "localhost").strip()
            pwd = quote_plus(self.pg_password or "", safe="")
            return (
                f"postgresql+psycopg://{quote_plus(user, safe='')}:{pwd}"
                f"@{host}:{self.pg_port}/{quote_plus(db, safe='')}"
            )
        return self.database_url

    @property
    def opensearch_effective_base_url(self) -> str | None:
        explicit = (self.opensearch_base_url or "").strip()
        if explicit:
            return explicit.rstrip("/")
        host = (self.opensearch_host or "").strip()
        if not host:
            return None
        scheme = "https" if self.opensearch_use_ssl else "http"
        return f"{scheme}://{host}:{self.opensearch_port}"

    @property
    def opensearch_auth(self) -> tuple[str, str] | None:
        user = (self.opensearch_user or "").strip()
        if not user:
            return None
        return (user, self.opensearch_password or "")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
