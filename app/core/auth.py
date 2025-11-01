"""
인증 관련 유틸리티 함수들
"""
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.adapters.supabase import get_supabase_client
from supabase import Client
from typing import Optional

security = HTTPBearer()

def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    현재 로그인한 사용자의 ID를 반환하는 의존성 함수.
    보호된 엔드포인트에서 사용할 수 있습니다.
    
    사용 예:
        @router.get("/protected")
        async def protected_endpoint(user_id: str = Depends(get_current_user_id)):
            ...
    """
    try:
        supabase: Client = get_supabase_client()
        user = supabase.auth.get_user(credentials.credentials)
        
        if user.user is None:
            raise HTTPException(
                status_code=401,
                detail="인증되지 않은 사용자입니다."
            )
        
        return user.user.id
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail="인증 토큰이 유효하지 않습니다."
        )

def get_optional_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security.auto_error(False))
) -> Optional[str]:
    """
    선택적 인증 의존성 함수. 토큰이 있으면 사용자 ID를 반환하고,
    없으면 None을 반환합니다.
    
    사용 예:
        @router.get("/optional-protected")
        async def optional_protected(user_id: Optional[str] = Depends(get_optional_user_id)):
            if user_id:
                # 로그인한 사용자용 로직
            else:
                # 비로그인 사용자용 로직
    """
    if credentials is None:
        return None
    
    try:
        supabase: Client = get_supabase_client()
        user = supabase.auth.get_user(credentials.credentials)
        
        if user.user is None:
            return None
        
        return user.user.id
    except Exception:
        return None

