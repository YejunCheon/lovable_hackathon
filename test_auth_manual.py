#!/usr/bin/env python3
"""
Auth API 수동 테스트 스크립트

사용법:
    python test_auth_manual.py

환경 변수:
    SUPABASE_URL과 SUPABASE_KEY가 .env 파일에 설정되어 있어야 합니다.
"""
import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

from httpx import AsyncClient
from app.main import app

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


async def test_signup(client: AsyncClient, email: str, password: str):
    """회원가입 테스트"""
    print("\n=== 회원가입 테스트 ===")
    response = await client.post(
        f"{BASE_URL}/v1/auth/signup",
        json={"email": email, "password": password}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response


async def test_signin(client: AsyncClient, email: str, password: str):
    """로그인 테스트"""
    print("\n=== 로그인 테스트 ===")
    response = await client.post(
        f"{BASE_URL}/v1/auth/signin",
        json={"email": email, "password": password}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        return response.json().get("access_token")
    return None


async def test_get_me(client: AsyncClient, token: str):
    """사용자 정보 조회 테스트"""
    print("\n=== 사용자 정보 조회 테스트 ===")
    response = await client.get(
        f"{BASE_URL}/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response


async def test_signout(client: AsyncClient, token: str):
    """로그아웃 테스트"""
    print("\n=== 로그아웃 테스트 ===")
    response = await client.post(
        f"{BASE_URL}/v1/auth/signout",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response


async def main():
    """메인 테스트 함수"""
    import random
    
    # 테스트용 이메일 생성
    test_email = f"test_{random.randint(100000, 999999)}@example.com"
    test_password = "test_password_123"
    
    print("=" * 60)
    print("Auth API 수동 테스트")
    print("=" * 60)
    print(f"테스트 이메일: {test_email}")
    print(f"테스트 비밀번호: {test_password}")
    
    async with AsyncClient(timeout=30.0) as client:
        try:
            # 1. 회원가입
            signup_response = await test_signup(client, test_email, test_password)
            
            if signup_response.status_code != 200:
                if "already registered" in signup_response.json().get("detail", "").lower():
                    print("\n⚠️  이미 존재하는 이메일입니다. 로그인으로 진행합니다.")
                else:
                    print("\n❌ 회원가입 실패")
                    return
            
            # 2. 로그인
            token = await test_signin(client, test_email, test_password)
            
            if not token:
                print("\n❌ 로그인 실패")
                return
            
            # 3. 사용자 정보 조회
            await test_get_me(client, token)
            
            # 4. 로그아웃
            await test_signout(client, token)
            
            print("\n" + "=" * 60)
            print("✅ 모든 테스트 완료!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    # 서버가 실행 중인지 확인
    if BASE_URL.startswith("http://localhost"):
        print("⚠️  서버가 실행 중인지 확인하세요: uvicorn app.main:app --reload")
        print()
    
    asyncio.run(main())

