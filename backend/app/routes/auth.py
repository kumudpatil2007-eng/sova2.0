import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, status
from pydantic import BaseModel

from ..services.auth_service import (
    has_users,
    create_user,
    verify_user,
    create_session,
    verify_session,
    revoke_session,
)

logger = logging.getLogger("sovereign_ai.auth_route")
router = APIRouter(prefix="/api/auth", tags=["auth"])


class SetupRequest(BaseModel):
    username: str
    password: str
    display_name: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


@router.get("/status")
async def auth_status():
    """Returns whether any local user exists on this SOVA node."""
    return {"has_users": has_users()}


@router.post("/setup")
async def setup_account(req: SetupRequest):
    """
    Creates a new local user account with an Argon2id password hash.
    Per sovereign architecture, credentials remain local to this machine.
    Does NOT auto-authenticate: user must return to the lock screen.
    """
    try:
        user_info = create_user(
            username=req.username,
            password=req.password,
            display_name=req.display_name
        )
        return {
            "success": True,
            "message": "Local workspace account created successfully.",
            "user": user_info
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error during user creation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Account setup failed.")


@router.post("/login")
async def login_endpoint(req: LoginRequest):
    """
    Authenticates user against local Argon2id password hash.
    If credentials do not match, returns a generic 'Incorrect username or password.' error
    without revealing whether username or password was the invalid factor.
    """
    user = verify_user(req.username, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password."
        )

    token = create_session(user)
    return {
        "success": True,
        "token": token,
        "user": user
    }


@router.post("/logout")
async def logout_endpoint(authorization: Optional[str] = Header(None)):
    """Revokes session and locks terminal."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ")[1].strip()
        revoke_session(token)
    return {"success": True, "message": "Logged out successfully."}


@router.get("/me")
async def me_endpoint(authorization: Optional[str] = Header(None)):
    """Validates active session."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = authorization.split("Bearer ")[1].strip()
    user = verify_session(token)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired or invalid")

    return {"authenticated": True, "user": user}
