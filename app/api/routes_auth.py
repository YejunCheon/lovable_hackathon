from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.auth import (
    SignUpRequest,
    SignUpResponse,
    SignInRequest,
    SignInResponse,
    UserResponse,
)
from app.adapters.supabase import get_supabase_client
from supabase import Client
import logging

router = APIRouter(tags=["Authentication"])
security = HTTPBearer()

@router.post("/auth/signup", response_model=SignUpResponse)
async def signup(request: SignUpRequest):
    """
    회원가입 엔드포인트
    """
    try:
        supabase: Client = get_supabase_client()
        
        # Supabase Auth로 회원가입
        response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
        })
        
        if response.user is None:
            raise HTTPException(
                status_code=400,
                detail="회원가입에 실패했습니다."
            )
        
        return SignUpResponse(
            user_id=response.user.id,
            email=response.user.email,
            message="회원가입이 완료되었습니다."
        )
    except Exception as e:
        logging.error(f"Signup error: {e}")
        if "already registered" in str(e).lower() or "already exists" in str(e).lower():
            raise HTTPException(
                status_code=400,
                detail="이미 등록된 이메일입니다."
            )
        raise HTTPException(
            status_code=500,
            detail=f"회원가입 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/auth/signin", response_model=SignInResponse)
async def signin(request: SignInRequest):
    """
    로그인 엔드포인트
    """
    try:
        supabase: Client = get_supabase_client()
        
        # Supabase Auth로 로그인
        response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password,
        })
        
        if response.user is None or response.session is None:
            raise HTTPException(
                status_code=401,
                detail="이메일 또는 비밀번호가 올바르지 않습니다."
            )
        
        return SignInResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            user={
                "id": response.user.id,
                "email": response.user.email,
            },
        )
    except Exception as e:
        logging.error(f"Signin error: {e}")
        raise HTTPException(
            status_code=401,
            detail="이메일 또는 비밀번호가 올바르지 않습니다."
        )

@router.get("/auth/me", response_model=UserResponse)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    현재 로그인한 사용자 정보 조회
    """
    try:
        supabase: Client = get_supabase_client()
        
        # 토큰으로 사용자 정보 조회
        user = supabase.auth.get_user(credentials.credentials)
        
        if user.user is None:
            raise HTTPException(
                status_code=401,
                detail="인증되지 않은 사용자입니다."
            )
        
        return UserResponse(
            id=user.user.id,
            email=user.user.email or "",
        )
    except Exception as e:
        logging.error(f"Get current user error: {e}")
        raise HTTPException(
            status_code=401,
            detail="인증 토큰이 유효하지 않습니다."
        )

@router.post("/auth/signout")
async def signout(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    로그아웃 엔드포인트
    """
    try:
        supabase: Client = get_supabase_client()
        
        # 현재 세션 설정 후 로그아웃
        supabase.auth.set_session(
            access_token=credentials.credentials,
            refresh_token=""  # refresh token이 필요하지만 여기서는 빈 값으로 처리
        )
        
        # 로그아웃 실행
        supabase.auth.sign_out()
        
        return {"message": "로그아웃되었습니다."}
    except Exception as e:
        logging.error(f"Signout error: {e}")
        # 로그아웃 실패해도 성공으로 처리 (토큰 무효화는 클라이언트에서 처리)
        return {"message": "로그아웃되었습니다."}

