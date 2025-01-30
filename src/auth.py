from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from fastapi import HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import logging
import requests

security = HTTPBearer()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def verify_google_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        logger.debug(f"Received access token: {token[:20]}...")
        
        # Use Google's tokeninfo endpoint
        response = requests.get(f'https://oauth2.googleapis.com/tokeninfo?id_token={token}')
        
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid token")
            
        token_info = response.json()
        # Extract user ID from token info
        user_id = token_info.get('sub')
        logger.debug(f"Verified user email: {user_id}")
        return user_id

    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))
