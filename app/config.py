"""
Configuration settings for the Contact API
"""
import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://localhost/contact_db"
    
    # AWS SES
    AWS_REGION: str = "us-east-2"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    SES_FROM_EMAIL: str = "no-reply@gizmodojp-line-bot.frwi.tech"
    ADMIN_EMAIL: str = "admin@example.com"
    
    # LINE
    LINE_CHANNEL_ID: str = ""
    
    # CORS
    LIFF_ORIGIN: str = "https://liff.line.me"
    ALLOWED_ORIGINS: str = "https://liff.line.me"
    
    # App
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
