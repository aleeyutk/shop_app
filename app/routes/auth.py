import secrets
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import User
from app.schemas import UserOut, MockLoginIn
from app.services.auth_service import (
    create_session_token,
    verify_session_token,
    get_google_auth_url,
    exchange_google_code_for_user_info,
    get_or_create_google_user,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()

SESSION_COOKIE_NAME = "novashop_session"
STATE_COOKIE_NAME = "novashop_oauth_state"


def get_current_user_optional(
    request: Request, db: Session = Depends(get_db)
) -> Optional[User]:
    """Dependency: retrieve current user from session cookie if present and valid."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        # Also check Authorization header for API clients: Bearer <token>
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]

    if not token:
        return None

    user_id = verify_session_token(token)
    if not user_id:
        return None

    return db.query(User).filter(User.id == user_id).first()


def get_current_user_required(
    user: Optional[User] = Depends(get_current_user_optional),
) -> User:
    """Dependency: enforce authenticated user."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in with Google.",
        )
    return user


@router.get("/google/login", summary="Initiate Google OAuth 2.0 Login")
def google_login(request: Request):
    """Redirects the user to Google's OAuth consent screen."""
    if not settings.is_google_auth_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Google OAuth is not configured. Please set GOOGLE_CLIENT_ID "
                "and GOOGLE_CLIENT_SECRET in your .env file or environment variables."
            ),
        )

    state = secrets.token_urlsafe(32)
    redirect_uri = f"{settings.BASE_URL.rstrip('/')}/auth/google/callback"
    auth_url = get_google_auth_url(redirect_uri=redirect_uri, state=state)

    response = RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key=STATE_COOKIE_NAME,
        value=state,
        httponly=True,
        max_age=300,  # 5 minutes
        samesite="lax",
    )
    return response


@router.get("/google/callback", summary="Google OAuth 2.0 Callback")
async def google_callback(
    request: Request,
    response: Response,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Handles the redirect back from Google OAuth consent screen."""
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google OAuth authorization rejected: {error}",
        )

    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing OAuth code in callback.",
        )

    saved_state = request.cookies.get(STATE_COOKIE_NAME)
    if not state or state != saved_state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OAuth state parameter (CSRF protection).",
        )

    redirect_uri = f"{settings.BASE_URL.rstrip('/')}/auth/google/callback"
    google_profile = await exchange_google_code_for_user_info(code, redirect_uri)
    if not google_profile or not google_profile.get("email"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to retrieve user profile from Google.",
        )

    user = get_or_create_google_user(db, google_profile)
    token = create_session_token(user.id)

    # Redirect to home with session cookie
    redirect = RedirectResponse(url="/?login=success", status_code=status.HTTP_302_FOUND)
    redirect.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=60 * 60 * 24 * 7,  # 7 days
        samesite="lax",
    )
    redirect.delete_cookie(STATE_COOKIE_NAME)
    return redirect


@router.get("/me", response_model=UserOut, summary="Get Current Authenticated User")
def get_current_user_profile(user: User = Depends(get_current_user_required)):
    """Return profile details for the currently logged in user."""
    return user


@router.post("/mock-login", response_model=UserOut, summary="Mock Login for Testing & Development")
def mock_login(
    payload: MockLoginIn,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Convenient mock authentication endpoint for local development, demoing, and automated tests.
    Creates or loads a test user and issues a valid session cookie.
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        user = User(
            google_id=f"mock-{secrets.token_hex(6)}",
            email=payload.email,
            name=payload.name,
            avatar_url=payload.avatar_url,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_session_token(user.id)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=60 * 60 * 24 * 7,
        samesite="lax",
    )
    user_out = UserOut.model_validate(user)
    user_out.token = token
    return user_out



@router.post("/logout", summary="Logout User")
def logout(response: Response):
    """Clears the session cookie."""
    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"message": "Successfully logged out."}
