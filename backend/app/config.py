from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    rag_top_k: int = 4
    abstain_score_threshold: float = 0.55
    corpus_dir: str = "data/corpus"

    chroma_host: str = "api.trychroma.com"
    chroma_api_key: str = ""
    chroma_tenant: str = ""
    chroma_database: str = "craftify_assignment"
    chroma_collection_docs: str = "craftify_docs"
    chroma_collection_tickets: str = "craftify_tickets"

    log_path: str = "../logs/tool_calls.jsonl"

    @property
    def corpus_path(self) -> Path:
        path = Path(self.corpus_dir)
        if not path.is_absolute():
            path = BACKEND_DIR / path
        return path

    @property
    def resolved_log_path(self) -> Path:
        path = Path(self.log_path)
        if not path.is_absolute():
            path = BACKEND_DIR / path
        return path

    @property
    def chroma_cloud_configured(self) -> bool:
        return bool(self.chroma_api_key and self.chroma_tenant and self.chroma_database)

    @property
    def deepseek_configured(self) -> bool:
        return bool(self.deepseek_api_key)


def get_settings() -> Settings:
    return Settings()
