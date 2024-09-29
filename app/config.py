import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "EthosNet"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    API_V1_STR: str = "/api/v1"
    
    # Server Settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Database Settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./ethosnet.db")
    
    # GaiaNet Settings
    GAIANET_API_URL: str = os.getenv("GAIANET_API_URL", "http://localhost:8080/v1")
    GAIANET_API_KEY: str = os.getenv("GAIANET_API_KEY", "")
    
    # Ethereum Settings
    ETHEREUM_NODE_URL: str = os.getenv("ETHEREUM_NODE_URL", "http://localhost:8545")
    ETHOSNET_CONTRACT_ADDRESS: str = os.getenv("ETHOSNET_CONTRACT_ADDRESS", "")
    
    # LLM Settings
    LLM_MODEL_PATH: str = os.getenv("LLM_MODEL_PATH", "./models/ethosnet_llm")
    
    # Vector Database Settings
    VECTOR_DB_URL: str = os.getenv("VECTOR_DB_URL", "http://localhost:6333")
    VECTOR_DB_COLLECTION: str = os.getenv("VECTOR_DB_COLLECTION", "ethosnet_knowledge")
    
    # JWT Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Logging Settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS Settings
    CORS_ORIGINS: list = [
        "http://localhost",
        "http://localhost:8080",
        "https://ethosnet.ai"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()