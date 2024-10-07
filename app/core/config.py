from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "EthosNet"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./ethosnet.db")

    # GaiaNet API
    GAIANET_API_URL: str = os.getenv("GAIANET_API_URL", "http://localhost:8080")
    GAIANET_API_KEY: str = os.getenv("GAIANET_API_KEY", "your-api-key")

    # Ethereum settings
    ETHEREUM_RPC_URL: str = os.getenv("ETHEREUM_RPC_URL", "https://mainnet.infura.io/v3/your-project-id")
    ETHOSNET_CONTRACT_ADDRESS: str = os.getenv("ETHOSNET_CONTRACT_ADDRESS", "0x...")

    # LLM settings
    LLM_MODEL_PATH: str = os.getenv("LLM_MODEL_PATH", "./models/ethosnet_llm")

    # Vector Database settings
    VECTOR_DB_URL: str = os.getenv("VECTOR_DB_URL", "http://localhost:6333")
    VECTOR_DB_API_KEY: str = os.getenv("VECTOR_DB_API_KEY", "your-qdrant-api-key")

    # JWT settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "https://ethosnet.ai",
    ]

    # Logging
    LOG_LEVEL: str = "INFO"

    # Reputation system settings
    MIN_REPUTATION_FOR_REVIEW: float = 50.0
    REPUTATION_CHANGE_FOR_REVIEW: float = 1.0
    REPUTATION_DECAY_THRESHOLD: int = 30  # days
    REPUTATION_DECAY_RATE: float = 0.01  # per day after threshold
    MAX_REPUTATION: float = 1000.0

    # Ethics evaluation settings
    MIN_STANDARD_QUALITY_SCORE: float = 70.0

    # Knowledge base settings
    KNOWLEDGE_ENTRY_MAX_LENGTH: int = 10000  # characters

    # Fine-tuning settings
    FINE_TUNING_BATCH_SIZE: int = 4
    FINE_TUNING_LEARNING_RATE: float = 2e-5
    FINE_TUNING_NUM_EPOCHS: int = 3

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()