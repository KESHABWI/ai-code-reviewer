from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, sourced from environment variables / .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "gpt-oss:20b-cloud"

    max_upload_mb: int = 50
    projects_dir: str = "/tmp/reviewer_projects"
    request_timeout_seconds: int = 300
    max_files_per_project: int = 200
    max_file_size_kb: int = 300
    review_concurrency: int = 3

    # "grep" = code-index-mcp (johnhuang316), "semantic" = cocoindex-code
    code_index_backend: str = "grep"
    # When true, every MCP and Ollama request/response is printed to stdout verbatim
    trace_io: bool = False

    # SQLite history database: analyzed repos/zips/files keyed by commit sha / content hash
    db_path: str = "/tmp/reviewer_projects/history.db"
    # Optional GitHub token, only needed to raise the 60 req/hr unauthenticated rate limit
    github_token: str = ""
    github_request_timeout_seconds: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
