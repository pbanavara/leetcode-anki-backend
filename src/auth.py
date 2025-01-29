from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

import requests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

security = HTTPBearer()

def verify_google_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        logger.debug(f"Received access token: {token[:20]}...")

        userinfo_endpoint = "https://www.googleapis.com/oauth2/v3/userinfo"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(userinfo_endpoint, headers=headers)
        userinfo = response.json()

        user_id = userinfo["sub"]
        logger.debug(f"Verified user ID: {user_id}")
        return user_id

    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(status_code=401, detail=str(e))