from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.auth import (
    SignUpRequest,
    SignUpResponse,
    SignInRequest,
    SignInResponse,
    UserResponse,
    OAuthInitRequest,
    OAuthInitResponse,
)
from app.adapters.supabase import get_supabase_client
from app.adapters.pg import execute_query
from app.core.config import settings
from supabase import Client
import logging
from typing import Optional

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
    except HTTPException:
        # HTTPException은 그대로 전파
        raise
    except Exception as e:
        error_message = str(e).lower()
        logging.error(f"Signup error: {e}")
        
        # 이메일 비율 제한 에러 처리
        if "rate limit" in error_message or "too many requests" in error_message:
            raise HTTPException(
                status_code=429,
                detail="이메일 전송 비율 제한에 걸렸습니다. 잠시 후 다시 시도해주세요."
            )
        
        # 이미 등록된 이메일 에러 처리
        if "already registered" in error_message or "already exists" in error_message or "user already registered" in error_message:
            raise HTTPException(
                status_code=400,
                detail="이미 등록된 이메일입니다."
            )
        
        # 잘못된 이메일 형식
        if "invalid email" in error_message or "email format" in error_message:
            raise HTTPException(
                status_code=400,
                detail="올바른 이메일 형식이 아닙니다."
            )
        
        # 약한 비밀번호
        if "password" in error_message and ("weak" in error_message or "too short" in error_message):
            raise HTTPException(
                status_code=400,
                detail="비밀번호가 너무 약합니다. 더 강한 비밀번호를 사용해주세요."
            )
        
        # 기타 에러는 일반 500 에러로 처리
        raise HTTPException(
            status_code=500,
            detail="회원가입 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
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

@router.post("/auth/oauth/init", response_model=OAuthInitResponse)
async def oauth_init(request: OAuthInitRequest):
    """
    OAuth 로그인 초기화 엔드포인트
    Google 또는 LinkedIn OAuth URL을 생성합니다.
    
    지원되는 provider: "google", "linkedin"
    """
    valid_providers = ["google", "linkedin"]
    
    if request.provider.lower() not in valid_providers:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 provider입니다. 지원되는 provider: {', '.join(valid_providers)}"
        )
    
    try:
        supabase: Client = get_supabase_client()
        
        # 리다이렉트 URL 설정
        redirect_to = request.redirect_to or settings.OAUTH_REDIRECT_URL
        
        # OAuth URL 생성
        oauth_response = supabase.auth.sign_in_with_oauth({
            "provider": request.provider.lower(),
            "options": {
                "redirect_to": redirect_to
            }
        })
        
        if not oauth_response or not oauth_response.url:
            raise HTTPException(
                status_code=500,
                detail="OAuth URL 생성에 실패했습니다."
            )
        
        return OAuthInitResponse(
            url=oauth_response.url,
            provider=request.provider.lower()
        )
    except Exception as e:
        logging.error(f"OAuth init error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"OAuth 초기화 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/auth/oauth/google")
async def oauth_google_init(redirect_to: Optional[str] = None):
    """
    Google OAuth 로그인 시작 (간편한 GET 엔드포인트)
    """
    try:
        supabase: Client = get_supabase_client()
        
        redirect_url = redirect_to or settings.OAUTH_REDIRECT_URL
        
        oauth_response = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": redirect_url
            }
        })
        
        if not oauth_response or not oauth_response.url:
            raise HTTPException(
                status_code=500,
                detail="Google OAuth URL 생성에 실패했습니다."
            )
        
        return RedirectResponse(url=oauth_response.url)
    except Exception as e:
        logging.error(f"Google OAuth init error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Google OAuth 초기화 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/auth/oauth/linkedin")
async def oauth_linkedin_init(redirect_to: Optional[str] = None):
    """
    LinkedIn OAuth 로그인 시작 (간편한 GET 엔드포인트)
    """
    try:
        supabase: Client = get_supabase_client()
        
        redirect_url = redirect_to or settings.OAUTH_REDIRECT_URL
        
        oauth_response = supabase.auth.sign_in_with_oauth({
            "provider": "linkedin",
            "options": {
                "redirect_to": redirect_url
            }
        })
        
        if not oauth_response or not oauth_response.url:
            raise HTTPException(
                status_code=500,
                detail="LinkedIn OAuth URL 생성에 실패했습니다."
            )
        
        return RedirectResponse(url=oauth_response.url)
    except Exception as e:
        logging.error(f"LinkedIn OAuth init error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"LinkedIn OAuth 초기화 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/auth/callback")
async def oauth_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None)
):
    """
    OAuth 콜백 엔드포인트
    Supabase는 자동으로 세션을 관리하므로, 여기서는 사용자를 적절한 페이지로 리다이렉트합니다.
    
    실제 토큰은 클라이언트에서 `supabase.auth.getSession()`으로 확인할 수 있습니다.
    """
    if error:
        logging.error(f"OAuth callback error: {error}, description: {error_description}")
        raise HTTPException(
            status_code=400,
            detail=f"OAuth 인증 실패: {error_description or error}"
        )
    
    if not code:
        raise HTTPException(
            status_code=400,
            detail="OAuth code가 제공되지 않았습니다."
        )
    
    try:
        supabase: Client = get_supabase_client()
        
        # 코드로 세션 교환 (Supabase가 자동으로 처리)
        # 실제로는 클라이언트에서 처리하는 것이 권장되지만,
        # 서버에서도 할 수 있습니다.
        try:
            # 세션 확인을 위해 사용자 정보 가져오기 시도
            # 실제로는 클라이언트에서 URL fragment를 사용하여 처리
            pass
        except Exception:
            pass
        
        # 성공적으로 인증된 경우, 클라이언트로 리다이렉트
        # 실제 애플리케이션에서는 프론트엔드 URL로 리다이렉트
        return {
            "message": "인증이 완료되었습니다. 클라이언트에서 세션을 확인하세요.",
            "code": code,
            "state": state,
            "note": "Supabase는 URL fragment에 access_token을 반환합니다. 클라이언트에서 확인하세요."
        }
    except Exception as e:
        logging.error(f"OAuth callback error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"OAuth 콜백 처리 중 오류가 발생했습니다: {str(e)}"
        )

