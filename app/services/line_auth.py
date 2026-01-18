"""
LINE ID Token verification service
"""
import time
import logging
from typing import Optional

import requests

from ..config import settings

logger = logging.getLogger(__name__)


def verify_id_token(id_token: str) -> Optional[str]:
    """
    Verify LINE ID token and return user ID
    
    Args:
        id_token: LINE ID token from LIFF
        
    Returns:
        LINE user ID if valid, None otherwise
    """
    if not id_token:
        return None
    
    try:
        response = requests.post(
            "https://api.line.me/oauth2/v2.1/verify",
            data={
                "id_token": id_token,
                "client_id": settings.LINE_CHANNEL_ID,
            },
            timeout=5,
        )
        
        if response.status_code != 200:
            logger.warning(f"LINE ID token verification failed: {response.status_code}")
            return None
        
        data = response.json()
        
        # Verify issuer
        if data.get("iss") != "https://access.line.me":
            logger.warning("Invalid issuer in LINE ID token")
            return None
        
        # Verify audience
        if data.get("aud") != settings.LINE_CHANNEL_ID:
            logger.warning("Invalid audience in LINE ID token")
            return None
        
        # Verify expiration
        if data.get("exp", 0) < int(time.time()):
            logger.warning("LINE ID token has expired")
            return None
        
        return data.get("sub")
        
    except requests.RequestException as e:
        logger.error(f"Error verifying LINE ID token: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error verifying LINE ID token: {e}")
        return None
