from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "YouTube Winning Pattern Detector"
    
    # Database
    DATABASE_URL: str
    
    # AgentBay
    AGENTBAY_API_KEY: str
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_BASE_URL: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
