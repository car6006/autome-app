import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import bcrypt
from jose import JWTError, jwt
from fastapi import HTTPException, Depends, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
database = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 24 * 60  # 24 hours

security = HTTPBearer()

def db():
    return database

class UserProfile(BaseModel):
    first_name: str = ""
    last_name: str = ""
    company: str = ""
    job_title: str = ""
    phone: str = ""
    bio: str = ""
    avatar_url: str = ""
    preferences: Dict[str, Any] = Field(default_factory=dict)

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    username: str
    hashed_password: str
    profile: UserProfile = Field(default_factory=UserProfile)
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None
    notes_count: int = 0
    total_time_saved: int = 0  # in minutes

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    first_name: str = ""
    last_name: str = ""

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    profile: UserProfile
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    notes_count: int
    total_time_saved: int

class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Create a JWT token"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        return await db()["users"].find_one({"email": email})
    
    @staticmethod
    async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        return await db()["users"].find_one({"username": username})
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        return await db()["users"].find_one({"id": user_id})
    
    @staticmethod
    async def create_user(user_data: UserCreate) -> str:
        """Create a new user"""
        # Check if email already exists
        if await AuthService.get_user_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if username already exists
        if await AuthService.get_user_by_username(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create user
        profile = UserProfile(
            first_name=user_data.first_name,
            last_name=user_data.last_name
        )
        
        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=AuthService.hash_password(user_data.password),
            profile=profile
        )
        
        await db()["users"].insert_one(user.dict())
        return user.id
    
    @staticmethod
    async def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password"""
        user = await AuthService.get_user_by_email(email)
        if not user:
            return None
        
        if not AuthService.verify_password(password, user["hashed_password"]):
            return None
        
        # Update last login
        await db()["users"].update_one(
            {"id": user["id"]},
            {"$set": {"last_login": datetime.now(timezone.utc)}}
        )
        
        return user
    
    @staticmethod
    async def update_user_profile(user_id: str, profile_data: UserProfileUpdate) -> bool:
        """Update user profile"""
        update_data = {}
        for field, value in profile_data.dict(exclude_unset=True).items():
            update_data[f"profile.{field}"] = value
        
        if update_data:
            result = await db()["users"].update_one(
                {"id": user_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        return False

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await AuthService.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

# Optional authentication (for endpoints that work with or without auth)
async def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    """Get current user if authenticated, None otherwise"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    try:
        # Create a mock credentials object
        from fastapi.security import HTTPAuthorizationCredentials
        token = authorization.split(" ")[1]
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        return await get_current_user(credentials)
    except (HTTPException, IndexError):
        return None