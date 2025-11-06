"""
IntelliDoc Pro - Configuration Settings
Centralized configuration management using Pydantic Settings
"""

from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application Configuration
    app_name: str = Field(default="IntelliDoc Pro", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    environment: str = Field(default="production", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=4, env="API_WORKERS")
    api_key_salt: str = Field(default="", env="API_KEY_SALT")

    # LLM Provider API Keys
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", env="ANTHROPIC_API_KEY")
    google_api_key: str = Field(default="", env="GOOGLE_API_KEY")

    # OCR Service API Keys
    aws_access_key_id: str = Field(default="", env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(default="", env="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field(default="us-east-1", env="AWS_REGION")
    google_cloud_project: str = Field(default="", env="GOOGLE_CLOUD_PROJECT")
    google_application_credentials: Optional[str] = Field(default=None, env="GOOGLE_APPLICATION_CREDENTIALS")

    # Vector Database Configuration
    chromadb_host: str = Field(default="localhost", env="CHROMADB_HOST")
    chromadb_port: int = Field(default=8001, env="CHROMADB_PORT")
    pinecone_api_key: str = Field(default="", env="PINECONE_API_KEY")
    pinecone_environment: str = Field(default="us-west1-gcp", env="PINECONE_ENVIRONMENT")

    # Database Configuration
    database_url: str = Field(default="postgresql://localhost/intellidoc", env="DATABASE_URL")
    mongodb_url: str = Field(default="mongodb://localhost:27017/intellidoc", env="MONGODB_URL")

    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    celery_broker_url: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/2", env="CELERY_RESULT_BACKEND")

    # Document Processing Configuration
    max_file_size_mb: int = Field(default=50, env="MAX_FILE_SIZE_MB")
    supported_formats: str = Field(default="pdf,png,jpg,jpeg,tiff,docx,xlsx", env="SUPPORTED_FORMATS")
    ocr_engine: str = Field(default="aws_textract", env="OCR_ENGINE")
    extraction_model: str = Field(default="gpt-4-turbo-preview", env="EXTRACTION_MODEL")

    # IRZ-CoT Configuration
    enable_role_based_prompting: bool = Field(default=True, env="ENABLE_ROLE_BASED_PROMPTING")
    enable_zero_shot_cot: bool = Field(default=True, env="ENABLE_ZERO_SHOT_COT")
    chain_of_thought_depth: int = Field(default=3, env="CHAIN_OF_THOUGHT_DEPTH")
    confidence_threshold: float = Field(default=0.85, env="CONFIDENCE_THRESHOLD")

    # Validation Configuration
    enable_rav: bool = Field(default=True, env="ENABLE_RAV")
    enable_rac: bool = Field(default=True, env="ENABLE_RAC")
    validation_sources: str = Field(default="wikipedia,sec_edgar,pubmed", env="VALIDATION_SOURCES")
    max_validation_attempts: int = Field(default=3, env="MAX_VALIDATION_ATTEMPTS")
    auto_correct_threshold: float = Field(default=0.90, env="AUTO_CORRECT_THRESHOLD")

    # Performance Configuration
    concurrent_processing_limit: int = Field(default=10, env="CONCURRENT_PROCESSING_LIMIT")
    processing_timeout_seconds: int = Field(default=300, env="PROCESSING_TIMEOUT_SECONDS")
    cache_ttl_seconds: int = Field(default=3600, env="CACHE_TTL_SECONDS")
    enable_batch_processing: bool = Field(default=True, env="ENABLE_BATCH_PROCESSING")

    # Security Configuration
    jwt_secret_key: str = Field(default="", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    encryption_key: str = Field(default="", env="ENCRYPTION_KEY")

    # Monitoring Configuration
    enable_prometheus: bool = Field(default=True, env="ENABLE_PROMETHEUS")
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    enable_structured_logging: bool = Field(default=True, env="ENABLE_STRUCTURED_LOGGING")

    # Storage Configuration
    storage_backend: str = Field(default="s3", env="STORAGE_BACKEND")
    s3_bucket_name: str = Field(default="intellidoc-documents", env="S3_BUCKET_NAME")
    gcs_bucket_name: str = Field(default="intellidoc-documents", env="GCS_BUCKET_NAME")
    azure_container_name: str = Field(default="intellidoc-documents", env="AZURE_CONTAINER_NAME")
    local_storage_path: str = Field(default="/var/intellidoc/storage", env="LOCAL_STORAGE_PATH")

    # Email Configuration
    smtp_host: str = Field(default="smtp.gmail.com", env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_user: str = Field(default="", env="SMTP_USER")
    smtp_password: str = Field(default="", env="SMTP_PASSWORD")
    email_from: str = Field(default="noreply@intellidoc.ai", env="EMAIL_FROM")

    # Webhook Configuration
    enable_webhooks: bool = Field(default=True, env="ENABLE_WEBHOOKS")
    webhook_retry_attempts: int = Field(default=3, env="WEBHOOK_RETRY_ATTEMPTS")
    webhook_timeout_seconds: int = Field(default=30, env="WEBHOOK_TIMEOUT_SECONDS")

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_requests_per_minute: int = Field(default=60, env="RATE_LIMIT_REQUESTS_PER_MINUTE")
    rate_limit_burst: int = Field(default=10, env="RATE_LIMIT_BURST")

    # Feature Flags
    feature_custom_models: bool = Field(default=True, env="FEATURE_CUSTOM_MODELS")
    feature_batch_upload: bool = Field(default=True, env="FEATURE_BATCH_UPLOAD")
    feature_real_time_streaming: bool = Field(default=True, env="FEATURE_REAL_TIME_STREAMING")
    feature_advanced_analytics: bool = Field(default=True, env="FEATURE_ADVANCED_ANALYTICS")

    @validator("chain_of_thought_depth")
    def validate_cot_depth(cls, v):
        """Ensure CoT depth is between 1 and 5"""
        if not 1 <= v <= 5:
            raise ValueError("chain_of_thought_depth must be between 1 and 5")
        return v

    @validator("confidence_threshold", "auto_correct_threshold")
    def validate_threshold(cls, v):
        """Ensure thresholds are between 0 and 1"""
        if not 0 <= v <= 1:
            raise ValueError("Threshold must be between 0 and 1")
        return v

    @property
    def supported_formats_list(self) -> List[str]:
        """Get supported formats as a list"""
        return [fmt.strip() for fmt in self.supported_formats.split(",")]

    @property
    def validation_sources_list(self) -> List[str]:
        """Get validation sources as a list"""
        return [src.strip() for src in self.validation_sources.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes"""
        return self.max_file_size_mb * 1024 * 1024

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance"""
    return settings
