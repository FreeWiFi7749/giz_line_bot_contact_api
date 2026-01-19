"""
Configuration settings for the Contact API
"""
import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://localhost/contact_db"
    
    # Resend (Email API)
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "Gizmodo Japan LINE Bot <no-reply@gizmodojp-line-bot.frwi.tech>"
    ADMIN_EMAIL: str = "admin@example.com"
    
    # LINE
    LINE_CHANNEL_ID: str = ""
    
    # Cloudflare Turnstile (human verification)
    TURNSTILE_SECRET_KEY: str = ""
    
    # CORS - LINE Mini App uses miniapp.line.me, legacy LIFF uses liff.line.me
    LIFF_ORIGIN: str = "https://miniapp.line.me"
    ALLOWED_ORIGINS: str = "https://liff.line.me,https://miniapp.line.me"
    
    # App
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
