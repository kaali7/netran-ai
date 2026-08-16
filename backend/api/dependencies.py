"""
Netran AI — FastAPI Dependency Injection Utilities.
Provides database sessions, OAuth2 authentication, WebSocket auth, and RBAC guards.
"""

from typing import Generator
from fastapi import Depends, HTTPException, status, Query, WebSocket
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from api.db import get_db
from api.models import User, UserRole
from api.security import decode_token

# OAuth2 bearer scheme for HTTP Authorization header (points to form-data OAuth2 token endpoint)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")



def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Validate bearer token and retrieve authenticated user profile."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = decode_token(token)
    if token_data is None or token_data.user_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception

    return user


async def get_ws_user(
    websocket: WebSocket,
    token: str = Query(..., description="JWT Bearer Token for WebSocket Handshake"),
    db: Session = Depends(get_db)
) -> User:
    """Extract and validate query-parameter authentication token for native WebSockets."""
    token_data = decode_token(token)
    if token_data is None or token_data.user_id is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(status_code=401, detail="Invalid WebSocket token")

    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(status_code=401, detail="User not found")

    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Enforce admin Role-Based Access Control (RBAC)."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user
