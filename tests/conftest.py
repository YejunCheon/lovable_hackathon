"""
pytest 설정 및 공통 픽스처
"""
import pytest
import os
from httpx import AsyncClient
from app.main import app

# 테스트용 환경 변수 설정
os.environ.setdefault("SUPABASE_URL", "https://test-project.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-anon-key")

@pytest.fixture
async def client():
    """
    FastAPI 테스트 클라이언트
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def test_email():
    """테스트용 이메일"""
    import random
    return f"test_{random.randint(1000, 9999)}@example.com"

@pytest.fixture
def test_password():
    """테스트용 비밀번호"""
    return "test_password_123"

@pytest.fixture
def test_user_data(test_email, test_password):
    """테스트용 사용자 데이터"""
    return {
        "email": test_email,
        "password": test_password
    }

