"""
JWT Authentication module for Grid Monitoring API
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Security configuration
SECRET_KEY = "grid-monitor-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()


class Token(BaseModel):
    """Token response model"""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data for JWT payload"""

    username: str
    exp: datetime


class User(BaseModel):
    """User model"""

    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    """User in database"""

    hashed_password: str


# Mock user database (replace with real DB in production)
fake_users_db: dict[str, UserInDB] = {
    "admin": UserInDB(
        username="admin",
        full_name="Grid Admin",
        email="admin@grid-monitor.com",
        hashed_password="$2b$12$QkSN1h1Ge.pHVzLHZUHiuuOKNjyzA6EC9GpDi0AGLtK2WYpbROW.K",  # secret
        disabled=False,
    )
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return bool(pwd_context.verify(plain_password, hashed_password))


def get_password_hash(password: str) -> str:
    """Hash password"""
    return str(pwd_context.hash(password))


def authenticate_user(
    fake_db: dict[str, UserInDB], username: str, password: str
) -> Optional[UserInDB]:
    """Authenticate user"""
    user = fake_db.get(username)
    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: Mapping[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = dict(data)
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = str(jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM))
    return encoded_jwt


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """Get current user from token"""
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        exp_value = payload.get("exp")
        if not isinstance(username, str) or not isinstance(exp_value, (int, float)):
            raise credential_exception
        token_data = TokenData(
            username=username,
            exp=datetime.fromtimestamp(exp_value, tz=timezone.utc),
        )
    except JWTError as exc:
        raise credential_exception from exc

    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credential_exception
    return user


def get_user(fake_db: dict[str, UserInDB], username: str) -> Optional[UserInDB]:
    """Get user from fake database"""
    return fake_db.get(username)
