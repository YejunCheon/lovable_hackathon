from supabase import create_client, Client
from app.core.config import settings

_supabase_client: Client | None = None

def get_supabase_client() -> Client:
    """Supabase 클라이언트 싱글톤 인스턴스 반환"""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _supabase_client

