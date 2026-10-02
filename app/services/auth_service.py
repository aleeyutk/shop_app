import logging
import urllib.parse
from typing import Optional, Dict, Any
import httpx
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sqlalchemy.orm import Session
from app.config import get_settings
from app.models import User

logger = logging.getLogger("shop.auth")
settings = get_settings()

serializer = URLSafeTimedSerializer(settings.SECRET_KEY, salt="shop-auth-session")


def create_session_token(user_id: int) -> str:
    """Create a signed session token containing the user ID."""
    return serializer.dumps({"user_id": user_id})


def verify_session_token(token: str, max_age_seconds: int = 60 * 60 * 24 * 7) -> Optional[int]:
    """Verify session token and return user_id if valid."""
    try:
        data = serializer.loads(token, max_age=max_age_seconds)
        return data.get("user_id")
    except (BadSignature, SignatureExpired):
        return None


def get_google_auth_url(redirect_uri: str, state: str) -> str:
    """Generate the Google OAuth 2.0 authorization URL."""
    base = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
        "state": state,
    }
    return f"{base}?{urllib.parse.urlencode(params)}"


async def exchange_google_code_for_user_info(code: str, redirect_uri: str) -> Optional[Dict[str, Any]]:
    """Exchange authorization code with Google for user tokens and fetch profile information."""
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        token_resp = await client.post(token_url, data=token_data)
        if token_resp.status_code != 200:
            logger.error("Failed to exchange Google OAuth code: %s", token_resp.text)
            return None

        tokens = token_resp.json()
        access_token = tokens.get("access_token")

        # Fetch Google user profile
        userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
        userinfo_resp = await client.get(
            userinfo_url,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo_resp.status_code != 200:
            logger.error("Failed to fetch Google userinfo: %s", userinfo_resp.text)
            return None

        return userinfo_resp.json()


def get_or_create_google_user(db: Session, google_profile: Dict[str, Any]) -> User:
    """Upsert user based on Google ID and email."""
    google_id = str(google_profile.get("sub"))
    email = google_profile.get("email")
    name = google_profile.get("name") or email.split("@")[0]
    avatar_url = google_profile.get("picture")

    user = db.query(User).filter((User.google_id == google_id) | (User.email == email)).first()

    if user:
        user.google_id = google_id
        user.name = name
        if avatar_url:
            user.avatar_url = avatar_url
    else:
        user = User(
            google_id=google_id,
            email=email,
            name=name,
            avatar_url=avatar_url,
        )
        db.add(user)

    db.commit()
    db.refresh(user)
    return user
