import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.models.user import User, UserRole
from app.models.external_identity import ExternalIdentity
from app.schemas.auth import GoogleAuthRequest, LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


def _session_for(user: User) -> TokenResponse:
    return TokenResponse(access_token=create_access_token(str(user.id)), user=user)


def _verify_google_credential(credential: str) -> dict:
    if not settings.google_client_id:
        raise HTTPException(status_code=503, detail={"code": "google_not_configured", "message": "Google sign-in is not configured on this server."})
    try:
        return id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            settings.google_client_id,
        )
    except Exception as exc:
        # Do not expose verifier internals to clients.
        raise HTTPException(status_code=401, detail={"code": "google_token_invalid", "message": "Google identity token could not be verified."}) from exc


@router.post("/register", response_model=UserResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if payload.role == UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin accounts cannot be self-registered")

    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        full_name=payload.full_name.strip(),
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")
    return _session_for(user)


@router.get("/google/status")
def google_status():
    """Safe public status endpoint; never exposes a client secret or raw client ID."""
    return {"configured": bool(settings.google_client_id)}


@router.post("/google", response_model=TokenResponse)
def google_login(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    claims = _verify_google_credential(payload.credential)

    if not claims.get("email_verified"):
        raise HTTPException(status_code=401, detail={"code": "google_email_unverified", "message": "Google email is not verified."})

    subject = str(claims.get("sub", "")).strip()
    email = str(claims.get("email", "")).lower().strip()
    full_name = str(claims.get("name") or (email.split("@")[0] if email else "Google user")).strip()
    if not subject or not email:
        raise HTTPException(status_code=401, detail={"code": "google_claims_missing", "message": "Google account did not provide the required identity claims."})

    identity = db.query(ExternalIdentity).filter(
        ExternalIdentity.provider == "google",
        ExternalIdentity.subject == subject,
    ).first()

    if identity:
        user = db.get(User, identity.user_id)
        if not user:
            raise HTTPException(status_code=401, detail={"code": "linked_account_missing", "message": "Linked MediLink account no longer exists."})
    else:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "google_link_required",
                    "message": "A MediLink account with this email already exists. Sign in with your password first. Google account linking can then be added from account settings.",
                },
            )

        role = payload.role
        if role not in (UserRole.patient, UserRole.doctor):
            raise HTTPException(
                status_code=428,
                detail={
                    "code": "role_required",
                    "message": "Choose Patient or Doctor to finish creating your MediLink account with Google.",
                },
            )

        user = User(
            full_name=full_name,
            email=email,
            hashed_password=hash_password(secrets.token_urlsafe(48)),
            role=role,
            is_active=True,
        )
        db.add(user)
        db.flush()
        db.add(ExternalIdentity(user_id=user.id, provider="google", subject=subject))
        db.commit()
        db.refresh(user)

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")
    return _session_for(user)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user
