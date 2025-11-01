"""
pytest 설정 및 공통 픽스처
"""
import pytest
import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport

# 테스트용 환경 변수 설정 (app.main import 전에 설정)
os.environ.setdefault("SUPABASE_URL", "https://test-project.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-anon-key")

# app.main을 나중에 import (가상환경 활성화 후)
def get_app():
    """지연 import를 위한 함수"""
    from app.main import app
    return app

@pytest.fixture
async def client():
    """
    FastAPI 테스트 클라이언트
    """
    app = get_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
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

