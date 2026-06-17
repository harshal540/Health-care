"""
STEP 5: SECURITY (PASSWORDS + JWT)
--------------------------------------
This file handles everything related to security:
1. Hashing and checking passwords (we NEVER store plain-text passwords)
2. Creating and reading JWT tokens (so a user stays "logged in")
3. Figuring out WHO is calling an endpoint, and WHAT ROLE they have

How JWT login works, in plain words:
  - User logs in with username + password.
  - If correct, we create a signed "token" (a long string) containing
    their user_id and role, and hand it to them.
  - On every future request, the user sends that token back in the
    "Authorization: Bearer <token>" header.
  - We verify the signature and trust the user_id/role inside it -
    no need to check the password again.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from . import models
from .database import get_db

# ---------------------------------------------------------------------------
# 1. SETTINGS
# ---------------------------------------------------------------------------
# In a REAL project, never hardcode the secret key. Load it from an
# environment variable instead, e.g.:
#   import os
#   SECRET_KEY = os.environ["SECRET_KEY"]
SECRET_KEY = "replace-this-with-a-long-random-string-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Tells FastAPI's docs page where to send login requests to get a token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# ---------------------------------------------------------------------------
# 2. PASSWORD HASHING
# ---------------------------------------------------------------------------
def hash_password(plain_password: str) -> str:
    """Turn a plain password into a secure, irreversible hash before saving it."""
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plain password against the stored hash, at login time."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


# ---------------------------------------------------------------------------
# 3. JWT TOKEN CREATION
# ---------------------------------------------------------------------------
def create_access_token(data: dict) -> str:
    """Create a signed JWT token that proves who the user is."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ---------------------------------------------------------------------------
# 4. READING THE TOKEN BACK (used to protect endpoints)
# ---------------------------------------------------------------------------
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """
    Every protected endpoint depends on this function.
    It reads the JWT token the client sent, decodes it, and returns
    the matching User row from the database.
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise credentials_error
    except JWTError:
        raise credentials_error

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise credentials_error
    return user


def require_role(role: str):
    """
    A dependency FACTORY. Example usage in a route:
        current_user: models.User = Depends(require_role("doctor"))
    This blocks anyone who is NOT a doctor from using that route.
    """
    def role_checker(current_user: models.User = Depends(get_current_user)) -> models.User:
        if current_user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Only users with role '{role}' can perform this action.",
            )
        return current_user
    return role_checker
