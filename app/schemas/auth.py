from pydantic import BaseModel, EmailStr
from typing import Optional

class SignUpRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class SignUpResponse(BaseModel):
    user_id: str
    email: str
    message: str

class SignInRequest(BaseModel):
    email: EmailStr
    password: str

class SignInResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: dict
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: str
    email: str

class OAuthInitRequest(BaseModel):
    provider: str  # "google" or "linkedin"
    redirect_to: Optional[str] = None

class OAuthInitResponse(BaseModel):
    url: str
    provider: str

class OAuthCallbackRequest(BaseModel):
    code: str
    state: Optional[str] = None

