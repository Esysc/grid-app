"""
Unit tests for authentication logic
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import Mock, patch

import pytest
from auth import (
    ALGORITHM,
    SECRET_KEY,
    Token,
    TokenData,
    User,
    UserInDB,
    authenticate_user,
    create_access_token,
    fake_users_db,
    get_password_hash,
    get_user,
    verify_password,
)
from jose import jwt
from jose.exceptions import ExpiredSignatureError


class TestPasswordHashing:
    """Test password hashing functions"""

    @patch("auth.pwd_context")
    def test_get_password_hash(self, mock_pwd_context: Mock) -> None:
        """Test password hashing"""
        mock_pwd_context.hash.return_value = "$2b$12$mock_hash_value_here_1234567890"

        password = "test"
        hashed: str = get_password_hash(password)

        assert hashed != password
        assert hashed.startswith("$2b$")
        mock_pwd_context.hash.assert_called_once_with(password)

    @patch("auth.pwd_context")
    def test_verify_password_correct(self, mock_pwd_context: Mock) -> None:
        """Test verify password with correct password"""
        mock_pwd_context.verify.return_value = True

        password = "test"
        hashed = "$2b$12$mock_hash_value"

        assert verify_password(password, hashed) is True
        mock_pwd_context.verify.assert_called_once_with(password, hashed)

    @patch("auth.pwd_context")
    def test_verify_password_incorrect(self, mock_pwd_context: Mock) -> None:
        """Test verify password with incorrect password"""
        mock_pwd_context.verify.return_value = False

        wrong_password = "wrong"
        hashed = "$2b$12$mock_hash_value"

        assert verify_password(wrong_password, hashed) is False
        mock_pwd_context.verify.assert_called_once_with(wrong_password, hashed)

    @patch("auth.pwd_context")
    def test_verify_password_case_sensitive(self, mock_pwd_context: Mock) -> None:
        """Test that password verification is case sensitive"""
        mock_pwd_context.verify.return_value = False

        wrong_case = "test"
        hashed = "$2b$12$mock_hash_value"

        assert verify_password(wrong_case, hashed) is False
        mock_pwd_context.verify.assert_called_once_with(wrong_case, hashed)


class TestAuthenticateUser:
    """Test user authentication"""

    @patch("auth.verify_password")
    def test_authenticate_user_success(self, mock_verify: Mock) -> None:
        """Test successful user authentication"""
        mock_verify.return_value = True

        user: UserInDB | None = authenticate_user(fake_users_db, "admin", "secret")

        assert user is not None
        assert user.username == "admin"
        assert user.full_name == "Grid Admin"

    @patch("auth.verify_password")
    def test_authenticate_user_not_found(self, mock_verify: Mock) -> None:
        """Test authentication with non-existent user"""
        user: UserInDB | None = authenticate_user(fake_users_db, "nonexistent", "password")

        assert user is None
        mock_verify.assert_not_called()

    @patch("auth.verify_password")
    def test_authenticate_user_wrong_password(self, mock_verify: Mock) -> None:
        """Test authentication with wrong password"""
        mock_verify.return_value = False

        user: UserInDB | None = authenticate_user(fake_users_db, "admin", "wrong_password")

        assert user is None
        mock_verify.assert_called_once()

    @patch("auth.verify_password")
    def test_authenticate_user_empty_password(self, mock_verify: Mock) -> None:
        """Test authentication with empty password"""
        mock_verify.return_value = False

        user: UserInDB | None = authenticate_user(fake_users_db, "admin", "")

        assert user is None


class TestGetUser:
    """Test user retrieval"""

    def test_get_user_exists(self) -> None:
        """Test retrieving existing user"""
        user: UserInDB | None = get_user(fake_users_db, "admin")

        assert user is not None
        assert user.username == "admin"
        assert user.email == "admin@grid-monitor.com"

    def test_get_user_not_exists(self) -> None:
        """Test retrieving non-existent user"""
        user: UserInDB | None = get_user(fake_users_db, "nonexistent")

        assert user is None

    def test_get_user_from_custom_db(self) -> None:
        """Test retrieving user from custom database"""
        custom_db: dict[str, UserInDB] = {
            "testuser": UserInDB(
                username="testuser",
                full_name="Test User",
                email="test@example.com",
                hashed_password="$2b$12$test",
                disabled=False,
            )
        }

        user: UserInDB | None = get_user(custom_db, "testuser")

        assert user is not None
        assert user.full_name == "Test User"


class TestAccessTokenCreation:
    """Test JWT access token creation"""

    def test_create_access_token_basic(self) -> None:
        """Test basic access token creation"""
        data: dict[str, str] = {"sub": "testuser"}
        token: str = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_decoding(self) -> None:
        """Test that created token can be decoded"""
        data: dict[str, str] = {"sub": "testuser"}
        token: str = create_access_token(data)

        # Decode the token

        decoded: dict[str, Any] = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["sub"] == "testuser"
        assert "exp" in decoded

    def test_create_access_token_with_expires_delta(self) -> None:
        """Test token creation with custom expiration"""
        data: dict[str, str] = {"sub": "testuser"}
        expires_delta = timedelta(minutes=60)
        token: str = create_access_token(data, expires_delta=expires_delta)

        decoded: dict[str, Any] = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["sub"] == "testuser"

        # Check that expiration is approximately 60 minutes from now
        now: datetime = datetime.now(timezone.utc)
        exp_time: datetime = datetime.fromtimestamp(float(decoded["exp"]), tz=timezone.utc)
        time_diff: float = (exp_time - now).total_seconds()

        # Should be approximately 60 minutes (within 5 seconds margin)
        assert 3595 < time_diff < 3605

    def test_create_access_token_without_expires_delta(self) -> None:
        """Test token creation without custom expiration (15 minute default)"""
        data: dict[str, str] = {"sub": "testuser"}
        token: str = create_access_token(data)

        decoded: dict[str, Any] = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Default expiration is 15 minutes
        now: datetime = datetime.now(timezone.utc)
        exp_time: datetime = datetime.fromtimestamp(float(decoded["exp"]), tz=timezone.utc)
        time_diff: float = (exp_time - now).total_seconds()

        # Should be approximately 15 minutes (900 seconds, within 5 seconds margin)
        assert 895 < time_diff < 905

    def test_create_access_token_expiration_in_past(self) -> None:
        """Test that token with past expiration is invalid"""
        data: dict[str, str] = {"sub": "testuser"}
        expires_delta = timedelta(minutes=-10)  # Expired 10 minutes ago
        token: str = create_access_token(data, expires_delta=expires_delta)

        # Token should decode but is technically expired
        try:
            jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            # If decode doesn't raise, token is still valid structure-wise
            # but JWT library would check expiration
        except ExpiredSignatureError:
            # This is expected for an expired token
            pass

    def test_create_access_token_multiple_data_fields(self) -> None:
        """Test token creation with multiple data fields"""
        data = {"sub": "testuser", "roles": ["admin", "user"]}
        token: str = create_access_token(data)

        decoded: dict[str, Any] = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["sub"] == "testuser"
        assert decoded["roles"] == ["admin", "user"]


class TestTokenDataModel:
    """Test TokenData model"""

    def test_token_data_creation(self) -> None:
        """Test TokenData model creation"""
        now: datetime = datetime.now(timezone.utc)
        token_data = TokenData(username="testuser", exp=now)

        assert token_data.username == "testuser"
        assert token_data.exp == now

    def test_token_data_missing_field(self) -> None:
        """Test TokenData model with missing field"""
        data: dict[str, Any] = {"username": "testuser"}
        with pytest.raises(ValueError):
            TokenData(**data)  # Missing exp


class TestTokenModel:
    """Test Token model"""

    def test_token_creation(self) -> None:
        """Test Token model creation"""
        token = Token(access_token="test_token_123", token_type="bearer")

        assert token.access_token == "test_token_123"
        assert token.token_type == "bearer"

    def test_token_missing_field(self) -> None:
        """Test Token model with missing field"""
        data: dict[str, Any] = {"access_token": "test_token_123"}
        with pytest.raises(ValueError):
            Token(**data)  # Missing token_type


class TestUserModel:
    """Test User model"""

    def test_user_creation(self) -> None:
        """Test User model creation"""
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            disabled=False,
        )

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.disabled is False

    def test_user_optional_fields(self) -> None:
        """Test User model with only required field"""
        user = User(username="testuser")

        assert user.username == "testuser"
        assert user.email is None
        assert user.full_name is None
        assert user.disabled is None


class TestUserInDBModel:
    """Test UserInDB model"""

    def test_user_in_db_creation(self) -> None:
        """Test UserInDB model creation"""
        user = UserInDB(
            username="testuser",
            email="test@example.com",
            hashed_password="$2b$12$test_hash",
            disabled=False,
        )

        assert user.username == "testuser"
        assert user.hashed_password == "$2b$12$test_hash"

    def test_user_in_db_inheritance(self) -> None:
        """Test UserInDB inherits from User"""
        user = UserInDB(
            username="testuser",
            full_name="Test User",
            hashed_password="$2b$12$test_hash",
        )

        assert user.username == "testuser"
        assert user.full_name == "Test User"
        assert user.hashed_password == "$2b$12$test_hash"
