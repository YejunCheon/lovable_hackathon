from pydantic import BaseModel, EmailStr

class SignUpRequest(BaseModel):
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

