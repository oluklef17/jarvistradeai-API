from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import os
from dotenv import load_dotenv

from database import get_db
from models_mysql import User
import logging

load_dotenv()

auth_logger = logging.getLogger("auth")
auth_logger.setLevel(logging.DEBUG)


# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token security
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=60)  # Extended from 15 to 60 minutes
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[str]:
    """Verify and decode a JWT token"""
    try:
        auth_logger.info(f"Attempting to verify token: {token[:20]}...")
        auth_logger.debug(f"Using SECRET_KEY: {SECRET_KEY}")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        auth_logger.debug(f"Token payload: {payload}")
        if user_id is None:
            auth_logger.warning("No user_id found in token")
            return None
        auth_logger.info(f"Successfully verified token for user: {user_id}")
        return user_id
    except JWTError as e:
        auth_logger.error(f"JWT verification failed: {e}")
        return None
    except Exception as e:
        auth_logger.error(f"Unexpected error during token verification: {e}")
        return None

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get the current authenticated user"""
    auth_logger.info(f"Authenticating user with token: {credentials.credentials[:20]}...")
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    user_id = verify_token(credentials.credentials)
    if user_id is None:
        auth_logger.warning("Token verification failed - no user_id found")
        raise credentials_exception
    
    auth_logger.info(f"Token verified for user_id: {user_id}")
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        auth_logger.error(f"User not found in database for user_id: {user_id}")
        raise credentials_exception
    
    auth_logger.info(f"User authenticated successfully: {user.email}")
    return user

async def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get the current authenticated user (optional - returns None if no token)"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ")[1]
        user_id = verify_token(token)
        if user_id is None:
            return None
        
        user = db.query(User).filter(User.id == user_id).first()
        return user
    except Exception:
        return None

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get the current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user with email and password"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

# For development purposes, create a simple user authentication
def create_user_if_not_exists(db: Session, email: str, password: str, is_admin: bool = False) -> User:
    """Create a user if they don't exist (for development)"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        hashed_password = get_password_hash(password)
        user = User(
            email=email,
            name="Admin User" if is_admin else "Regular User",
            hashed_password=hashed_password,
            is_admin=is_admin
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user 