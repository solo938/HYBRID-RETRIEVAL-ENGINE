from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Literal
from pathlib import Path

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    # API & Server
    APP_NAME: str = "Hybrid Retrieval Engine"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_NAME: str = "documents"
    
    # Elasticsearch (optional, keep for now)
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    ELASTICSEARCH_API_KEY: Optional[str] = None
    ELASTICSEARCH_INDEX_NAME: str = "documents"
    
    # BM25 index path
    BM25_INDEX_PATH: Optional[Path] = None          # <-- ADD THIS LINE
    
    # Models – SMALL for fast iteration
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIMENSION: int = 384
    RERANKER_MODEL_NAME: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    # LLM – only OpenAI for now
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL_NAME: str = "gpt-3.5-turbo"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 1024
    
    # Chunking
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 100
    
    # Retrieval
    DEFAULT_TOP_K: int = 10
    DENSE_TOP_K: int = 20
    SPARSE_TOP_K: int = 20
    FINAL_TOP_K: int = 10
    RRF_K: int = 60
    DENSE_WEIGHT: float = 0.5
    SPARSE_WEIGHT: float = 0.5
    
    # Embedding batching
    EMBEDDING_BATCH_SIZE: int = 32
    
    # Security toggles
    PII_DETECTION_ENABLED: bool = True
    HALLUCINATION_GUARD_ENABLED: bool = False
    
    # Observability
    LOG_LEVEL: Literal["DEBUG","INFO","WARNING","ERROR"] = "INFO"
    PROMETHEUS_ENABLED: bool = True
    
    # Cost / cache
    TOKEN_BUDGET: int = 4000
    SEMANTIC_CACHE_TTL_SECONDS: int = 3600
    
    def model_post_init(self, __context):
        if abs(self.DENSE_WEIGHT + self.SPARSE_WEIGHT - 1.0) > 1e-6:
            raise ValueError("DENSE_WEIGHT + SPARSE_WEIGHT must equal 1.0")
        return self

settings = Settings()