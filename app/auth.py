import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
)

from pydantic import BaseModel

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    create_engine,
)

from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
)

from app.config import get_settings


# ============================================================
# CONFIG
# ============================================================

settings = get_settings()

if not settings.database_url:
    raise RuntimeError(
        "DATABASE_URL is not configured in backend/.env"
    )

DATABASE_URL = settings.database_url

JWT_SECRET = settings.jwt_secret

JWT_ALGORITHM = "HS256"

JWT_EXPIRE_MINUTES = 120


# ============================================================
# DATABASE
# ============================================================

auth_engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

AuthBase = declarative_base()

AuthSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=auth_engine
)


# ============================================================
# USER MODEL
# ============================================================

class User(AuthBase):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    name = Column(
        String(100),
        nullable=False
    )

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = Column(
        String(500),
        nullable=False
    )

    role = Column(
        String(20),
        nullable=False,
        default="EMPLOYEE"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )


# Create users table if it does not exist
AuthBase.metadata.create_all(
    bind=auth_engine
)


# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(password: str) -> str:

    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        120000
    )

    return (
        salt.hex()
        + ":"
        + password_hash.hex()
    )


def verify_password(
    password: str,
    stored_hash: str
) -> bool:

    try:

        salt_hex, hash_hex = stored_hash.split(":")

        salt = bytes.fromhex(salt_hex)

        expected_hash = bytes.fromhex(hash_hex)

        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            120000
        )

        return hmac.compare_digest(
            actual_hash,
            expected_hash
        )

    except Exception:

        return False


# ============================================================
# JWT
# ============================================================

def create_access_token(user: User) -> str:

    expire = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=JWT_EXPIRE_MINUTES
        )
    )

    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "name": user.name,
        "exp": expire
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )


# ============================================================
# SCHEMAS
# ============================================================

class LoginRequest(BaseModel):

    email: str
    password: str


class UserResponse(BaseModel):

    id: int
    name: str
    email: str
    role: str


class LoginResponse(BaseModel):

    access_token: str
    token_type: str
    user: UserResponse


# ============================================================
# SECURITY
# ============================================================

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials =
        Depends(security)
):

    token = credentials.credentials

    try:

        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )

        user_id = payload.get("sub")

        if not user_id:

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )

    except jwt.ExpiredSignatureError:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )

    except jwt.InvalidTokenError:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

    db = AuthSessionLocal()

    try:

        user = (
            db.query(User)
            .filter(User.id == int(user_id))
            .first()
        )

        if not user:

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        return user

    finally:

        db.close()


# ============================================================
# ROLE CHECK
# ============================================================

def require_role(*allowed_roles):

    def role_checker(
        current_user: User =
            Depends(get_current_user)
    ):

        if current_user.role not in allowed_roles:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action"
            )

        return current_user

    return role_checker


# ============================================================
# AUTH ROUTER
# ============================================================

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# ============================================================
# LOGIN
# ============================================================

@router.post(
    "/login",
    response_model=LoginResponse
)
def login(data: LoginRequest):

    db = AuthSessionLocal()

    try:

        email = data.email.strip().lower()

        user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        if not user:

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        if not verify_password(
            data.password,
            user.password_hash
        ):

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        token = create_access_token(user)

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role
            }
        }

    finally:

        db.close()


# ============================================================
# CURRENT USER
# ============================================================

@router.get(
    "/me",
    response_model=UserResponse
)
def get_me(
    current_user: User =
        Depends(get_current_user)
):

    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role
    }


# ============================================================
# DEVELOPMENT USER SETUP
# ============================================================

@router.post(
    "/setup-users"
)
def setup_users():

    db = AuthSessionLocal()

    try:

        existing = db.query(User).count()

        if existing > 0:

            return {
                "message": "Users already exist",
                "count": existing
            }

        users = [

            User(
                name="Manju Employee",
                email="employee@supportflow.com",
                password_hash=hash_password(
                    "employee123"
                ),
                role="EMPLOYEE"
            ),

            User(
                name="IT Resolver",
                email="resolver@supportflow.com",
                password_hash=hash_password(
                    "resolver123"
                ),
                role="RESOLVER"
            ),

            User(
                name="System Admin",
                email="admin@supportflow.com",
                password_hash=hash_password(
                    "admin123"
                ),
                role="ADMIN"
            )

        ]

        db.add_all(users)

        db.commit()

        return {
            "message": "Default users created",
            "users": [
                {
                    "email": "employee@supportflow.com",
                    "role": "EMPLOYEE"
                },
                {
                    "email": "resolver@supportflow.com",
                    "role": "RESOLVER"
                },
                {
                    "email": "admin@supportflow.com",
                    "role": "ADMIN"
                }
            ]
        }

    finally:

        db.close()



# ============================================================
# ROLE DEPENDENCIES
# ============================================================

def employee_only(
    current_user: User =
        Depends(get_current_user)
):
    if current_user.role != "EMPLOYEE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Employee access required"
        )

    return current_user


def resolver_only(
    current_user: User =
        Depends(get_current_user)
):
    if current_user.role != "RESOLVER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Resolver access required"
        )

    return current_user


def admin_only(
    current_user: User =
        Depends(get_current_user)
):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return current_user


def resolver_or_admin(
    current_user: User =
        Depends(get_current_user)
):
    if current_user.role not in ["RESOLVER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Resolver or Admin access required"
        )

    return current_user


# ============================================================
# ADMIN - USER MANAGEMENT
# ============================================================

class CreateUserRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str


# ------------------------------------------------------------
# GET ALL USERS
# ------------------------------------------------------------

@router.get("/users")
def get_all_users(
    current_user: User = Depends(admin_only)
):
    db = AuthSessionLocal()

    try:
        users = (
            db.query(User)
            .order_by(User.id.desc())
            .all()
        )

        return [
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "created_at": user.created_at
            }
            for user in users
        ]

    finally:
        db.close()


# ------------------------------------------------------------
# CREATE USER
# ------------------------------------------------------------

@router.post("/users", status_code=201)
def create_user(
    data: CreateUserRequest,
    current_user: User = Depends(admin_only)
):
    db = AuthSessionLocal()

    try:
        email = data.email.strip().lower()
        role = data.role.strip().upper()

        # Validate role
        if role not in ["EMPLOYEE", "RESOLVER", "ADMIN"]:
            raise HTTPException(
                status_code=400,
                detail="Role must be EMPLOYEE, RESOLVER or ADMIN"
            )

        # Check existing user
        existing_user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="User with this email already exists"
            )

        # Validate password
        if len(data.password) < 6:
            raise HTTPException(
                status_code=400,
                detail="Password must contain at least 6 characters"
            )

        new_user = User(
            name=data.name.strip(),
            email=email,
            password_hash=hash_password(data.password),
            role=role
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "message": "User created successfully",
            "user": {
                "id": new_user.id,
                "name": new_user.name,
                "email": new_user.email,
                "role": new_user.role
            }
        }

    finally:
        db.close()


# ------------------------------------------------------------
# DELETE USER
# ------------------------------------------------------------

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(admin_only)
):
    db = AuthSessionLocal()

    try:
        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # Prevent admin from deleting their own account
        if user.id == current_user.id:
            raise HTTPException(
                status_code=400,
                detail="You cannot delete your own account"
            )

        db.delete(user)
        db.commit()

        return {
            "message": "User deleted successfully"
        }

    finally:
        db.close()