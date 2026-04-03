from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import firebase_admin
from firebase_admin import auth as fb_auth, credentials

bearer_scheme = HTTPBearer(auto_error=False)

# Initialize once (module import time)
if not firebase_admin._apps:
    firebase_admin.initialize_app()  # uses GOOGLE_APPLICATION_CREDENTIALS or default credentials


def get_firebase_identity(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token"
        )

    token = creds.credentials
    try:
        claims = fb_auth.verify_id_token(token)
        # claims contains: uid (as 'uid'), email (maybe), etc.
        return claims
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )
