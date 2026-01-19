"""
Cloudflare Turnstile verification service
"""
import logging
import httpx

from ..config import settings

logger = logging.getLogger(__name__)

TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


async def verify_turnstile_token(token: str) -> bool:
    """
    Verify a Cloudflare Turnstile token
    
    Args:
        token: The Turnstile response token from the frontend
        
    Returns:
        True if verification succeeds, False otherwise
    """
    if not settings.TURNSTILE_SECRET_KEY:
        logger.warning("TURNSTILE_SECRET_KEY not configured, skipping verification")
        return True
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                TURNSTILE_VERIFY_URL,
                data={
                    "secret": settings.TURNSTILE_SECRET_KEY,
                    "response": token,
                },
                timeout=10.0,
            )
            
            result = response.json()
            success = result.get("success", False)
            
            if not success:
                error_codes = result.get("error-codes", [])
                logger.warning(f"Turnstile verification failed: {error_codes}")
            
            return success
            
    except Exception as e:
        logger.error(f"Turnstile verification error: {e}")
        return False
