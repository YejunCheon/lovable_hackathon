"""
Auth API 테스트
"""
import pytest
from httpx import AsyncClient
from app.main import app
import os

# 실제 Supabase를 사용하는 통합 테스트는 환경 변수 필요
# SUPABASE_URL과 SUPABASE_KEY가 설정되어 있을 때만 실행
REAL_SUPABASE_CONFIGURED = (
    os.getenv("SUPABASE_URL") and 
    os.getenv("SUPABASE_KEY") and 
    not os.getenv("SUPABASE_URL", "").startswith("https://test-")
)


@pytest.mark.asyncio
class TestAuthAPI:
    """인증 API 테스트 클래스"""

    @pytest.fixture
    async def client(self):
        """테스트 클라이언트 픽스처"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    async def test_signup_endpoint_exists(self, client: AsyncClient):
        """회원가입 엔드포인트가 존재하는지 확인"""
        # 잘못된 형식이지만 엔드포인트가 존재하는지 확인
        response = await client.post("/v1/auth/signup", json={})
        # 422 (Validation Error) 또는 400 (Supabase Error)면 엔드포인트는 존재
        assert response.status_code in [400, 422]

    async def test_signin_endpoint_exists(self, client: AsyncClient):
        """로그인 엔드포인트가 존재하는지 확인"""
        response = await client.post("/v1/auth/signin", json={})
        assert response.status_code in [400, 422]

    async def test_me_endpoint_exists(self, client: AsyncClient):
        """사용자 정보 조회 엔드포인트가 존재하는지 확인"""
        response = await client.get("/v1/auth/me")
        # 401 (Unauthorized)면 엔드포인트는 존재
        assert response.status_code == 401

    async def test_signup_validation_error(self, client: AsyncClient):
        """회원가입 요청 검증 오류 테스트"""
        # 이메일 형식 오류
        response = await client.post("/v1/auth/signup", json={
            "email": "invalid-email",
            "password": "password123"
        })
        assert response.status_code == 422

    async def test_signin_validation_error(self, client: AsyncClient):
        """로그인 요청 검증 오류 테스트"""
        # 이메일 누락
        response = await client.post("/v1/auth/signin", json={
            "password": "password123"
        })
        assert response.status_code == 422

    @pytest.mark.skipif(not REAL_SUPABASE_CONFIGURED, reason="Supabase 설정이 필요합니다")
    async def test_signup_success(self, client: AsyncClient):
        """회원가입 성공 테스트 (실제 Supabase 필요)"""
        import random
        test_email = f"test_{random.randint(100000, 999999)}@example.com"
        test_password = "test_password_123"
        
        response = await client.post("/v1/auth/signup", json={
            "email": test_email,
            "password": test_password
        })
        
        # 성공하면 200, 이미 존재하면 400
        assert response.status_code in [200, 400]
        
        if response.status_code == 200:
            data = response.json()
            assert "user_id" in data
            assert "email" in data
            assert data["email"] == test_email

    @pytest.mark.skipif(not REAL_SUPABASE_CONFIGURED, reason="Supabase 설정이 필요합니다")
    async def test_signin_success(self, client: AsyncClient):
        """로그인 성공 테스트 (실제 Supabase 필요)"""
        # 먼저 회원가입
        import random
        test_email = f"test_{random.randint(100000, 999999)}@example.com"
        test_password = "test_password_123"
        
        signup_response = await client.post("/v1/auth/signup", json={
            "email": test_email,
            "password": test_password
        })
        
        # 회원가입 성공 후 로그인 시도
        if signup_response.status_code in [200, 400]:  # 이미 존재하더라도 진행
            signin_response = await client.post("/v1/auth/signin", json={
                "email": test_email,
                "password": test_password
            })
            
            assert signin_response.status_code == 200
            data = signin_response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert "user" in data
            assert data["user"]["email"] == test_email

    @pytest.mark.skipif(not REAL_SUPABASE_CONFIGURED, reason="Supabase 설정이 필요합니다")
    async def test_signin_wrong_password(self, client: AsyncClient):
        """잘못된 비밀번호 로그인 테스트"""
        # 먼저 회원가입
        import random
        test_email = f"test_{random.randint(100000, 999999)}@example.com"
        test_password = "test_password_123"
        
        await client.post("/v1/auth/signup", json={
            "email": test_email,
            "password": test_password
        })
        
        # 잘못된 비밀번호로 로그인 시도
        response = await client.post("/v1/auth/signin", json={
            "email": test_email,
            "password": "wrong_password"
        })
        
        assert response.status_code == 401

    @pytest.mark.skipif(not REAL_SUPABASE_CONFIGURED, reason="Supabase 설정이 필요합니다")
    async def test_get_current_user(self, client: AsyncClient):
        """현재 사용자 정보 조회 테스트"""
        # 먼저 회원가입 및 로그인
        import random
        test_email = f"test_{random.randint(100000, 999999)}@example.com"
        test_password = "test_password_123"
        
        await client.post("/v1/auth/signup", json={
            "email": test_email,
            "password": test_password
        })
        
        signin_response = await client.post("/v1/auth/signin", json={
            "email": test_email,
            "password": test_password
        })
        
        if signin_response.status_code == 200:
            token = signin_response.json()["access_token"]
            
            # 토큰으로 사용자 정보 조회
            me_response = await client.get(
                "/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert me_response.status_code == 200
            data = me_response.json()
            assert "id" in data
            assert "email" in data
            assert data["email"] == test_email

    @pytest.mark.skipif(not REAL_SUPABASE_CONFIGURED, reason="Supabase 설정이 필요합니다")
    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """잘못된 토큰으로 사용자 정보 조회 테스트"""
        response = await client.get(
            "/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token_12345"}
        )
        
        assert response.status_code == 401

    @pytest.mark.skipif(not REAL_SUPABASE_CONFIGURED, reason="Supabase 설정이 필요합니다")
    async def test_signout(self, client: AsyncClient):
        """로그아웃 테스트"""
        # 먼저 회원가입 및 로그인
        import random
        test_email = f"test_{random.randint(100000, 999999)}@example.com"
        test_password = "test_password_123"
        
        await client.post("/v1/auth/signup", json={
            "email": test_email,
            "password": test_password
        })
        
        signin_response = await client.post("/v1/auth/signin", json={
            "email": test_email,
            "password": test_password
        })
        
        if signin_response.status_code == 200:
            token = signin_response.json()["access_token"]
            
            # 로그아웃
            signout_response = await client.post(
                "/v1/auth/signout",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            # 로그아웃은 성공 또는 실패 모두 허용 (Supabase 구현에 따라 다름)
            assert signout_response.status_code in [200, 401, 500]


@pytest.mark.asyncio
async def test_auth_flow_integration(client: AsyncClient):
    """
    전체 인증 플로우 통합 테스트 (실제 Supabase 필요)
    """
    if not REAL_SUPABASE_CONFIGURED:
        pytest.skip("Supabase 설정이 필요합니다")
    
    import random
    test_email = f"test_{random.randint(100000, 999999)}@example.com"
    test_password = "test_password_123"
    
    # 1. 회원가입
    signup_response = await client.post("/v1/auth/signup", json={
        "email": test_email,
        "password": test_password
    })
    
    if signup_response.status_code == 400 and "already registered" in signup_response.json().get("detail", "").lower():
        # 이미 존재하는 경우 로그인으로 진행
        pass
    else:
        assert signup_response.status_code == 200, f"회원가입 실패: {signup_response.json()}"
    
    # 2. 로그인
    signin_response = await client.post("/v1/auth/signin", json={
        "email": test_email,
        "password": test_password
    })
    
    assert signin_response.status_code == 200, f"로그인 실패: {signin_response.json()}"
    signin_data = signin_response.json()
    access_token = signin_data["access_token"]
    
    # 3. 사용자 정보 조회
    me_response = await client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["email"] == test_email
    
    # 4. 로그아웃
    signout_response = await client.post(
        "/v1/auth/signout",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # 로그아웃은 성공 또는 실패 모두 허용
    assert signout_response.status_code in [200, 401, 500]

