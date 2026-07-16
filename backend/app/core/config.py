"""Application configuration via environment variables (12-factor)."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Radiografia AI API"
    environment: str = "development"

    # Persistence. Defaults to local SQLite so the API runs with zero infra;
    # docker-compose overrides this with PostgreSQL.
    database_url: str = "sqlite:///./radiografia.db"

    # Auth / JWT
    secret_key: str = "change-me-in-production-please-use-a-long-random-value"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 8

    # Object storage (local dir for MVP; swap for S3/MinIO in production).
    storage_dir: str = "./storage"

    # Secret salt for DICOM PHI pseudonymization. MUST be set (and kept secret)
    # in production; the same salt yields stable pseudonyms across uploads.
    deident_salt: str = "change-me-deident-salt"

    # Inference backend:
    #   "mock"  — deterministic, no ML deps (default)
    #   "xrv"   — TorchXRayVision pretrained DenseNet (real chest X-ray reading)
    #   "torch" — our own trained checkpoint (see ml/training)
    ml_backend: str = "mock"
    model_checkpoint: str = "./ml/inference/checkpoints/cxr-densenet-v0.1.0.pt"
    model_version_name: str = "cxr-densenet-v0.1.0"

    # TorchXRayVision weights id (used when ML_BACKEND=xrv).
    xrv_weights: str = "densenet121-res224-all"

    # First-run seed user (a radiologist who can review studies).
    seed_admin_email: str = "radiologista@example.com"
    seed_admin_password: str = "changeme123"

    # First-run governance user (can manage clinical policies).
    seed_governance_email: str = "governanca@example.com"
    seed_governance_password: str = "changeme123"


@lru_cache
def get_settings() -> Settings:
    return Settings()
