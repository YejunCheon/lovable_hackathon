# Auth API 테스트 가이드

이 문서는 Supabase를 사용한 인증 API를 테스트하는 방법을 안내합니다.

## 목차

1. [API 엔드포인트 목록](#api-엔드포인트-목록)
2. [환경 설정](#환경-설정)
3. [curl을 사용한 테스트](#curl을-사용한-테스트)
4. [Python 테스트 코드 실행](#python-테스트-코드-실행)
5. [Postman/Thunder Client 사용](#postmanthunder-client-사용)

---

## API 엔드포인트 목록

### 1. 회원가입
- **URL**: `POST /v1/auth/signup`
- **인증**: 불필요
- **요청 본문**:
  ```json
  {
    "email": "user@example.com",
    "password": "password123"
  }
  ```
- **응답 예시**:
  ```json
  {
    "user_id": "uuid-here",
    "email": "user@example.com",
    "message": "회원가입이 완료되었습니다."
  }
  ```

### 2. 로그인
- **URL**: `POST /v1/auth/signin`
- **인증**: 불필요
- **요청 본문**:
  ```json
  {
    "email": "user@example.com",
    "password": "password123"
  }
  ```
- **응답 예시**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "refresh-token-here",
    "user": {
      "id": "uuid-here",
      "email": "user@example.com"
    },
    "token_type": "bearer"
  }
  ```

### 3. 현재 사용자 정보 조회
- **URL**: `GET /v1/auth/me`
- **인증**: 필요 (Bearer Token)
- **응답 예시**:
  ```json
  {
    "id": "uuid-here",
    "email": "user@example.com"
  }
  ```

### 4. 로그아웃
- **URL**: `POST /v1/auth/signout`
- **인증**: 필요 (Bearer Token)
- **응답 예시**:
  ```json
  {
    "message": "로그아웃되었습니다."
  }
  ```

---

## 환경 설정

### 1. Supabase 프로젝트 설정

1. [Supabase](https://supabase.com)에서 프로젝트 생성
2. 프로젝트 설정 > API에서 다음 정보 확인:
   - `SUPABASE_URL`: `https://your-project.supabase.co`
   - `SUPABASE_KEY`: `anon` 또는 `service_role` 키

### 2. 환경 변수 설정

프로젝트 루트의 `.env` 파일에 추가:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
```

### 3. 서버 실행

```bash
# 가상환경 활성화
source venv/bin/activate

# 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## curl을 사용한 테스트

### 1. 회원가입

```bash
curl -X POST "http://localhost:8000/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test_password_123"
  }'
```

**성공 응답** (200):
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "test@example.com",
  "message": "회원가입이 완료되었습니다."
}
```

**실패 응답** (400 - 이미 존재하는 이메일):
```json
{
  "detail": "이미 등록된 이메일입니다."
}
```

### 2. 로그인

```bash
curl -X POST "http://localhost:8000/v1/auth/signin" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test_password_123"
  }'
```

**성공 응답** (200):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "refresh-token-here",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "test@example.com"
  },
  "token_type": "bearer"
}
```

**실패 응답** (401):
```json
{
  "detail": "이메일 또는 비밀번호가 올바르지 않습니다."
}
```

### 3. 사용자 정보 조회

```bash
# 로그인 후 받은 access_token 사용
TOKEN="your-access-token-here"

curl -X GET "http://localhost:8000/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

**성공 응답** (200):
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "test@example.com"
}
```

**실패 응답** (401):
```json
{
  "detail": "인증 토큰이 유효하지 않습니다."
}
```

### 4. 로그아웃

```bash
TOKEN="your-access-token-here"

curl -X POST "http://localhost:8000/v1/auth/signout" \
  -H "Authorization: Bearer $TOKEN"
```

**성공 응답** (200):
```json
{
  "message": "로그아웃되었습니다."
}
```

### 5. 전체 플로우 예시

```bash
# 1. 회원가입
SIGNUP_RESPONSE=$(curl -s -X POST "http://localhost:8000/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "secure_password_123"
  }')

echo "회원가입 응답: $SIGNUP_RESPONSE"

# 2. 로그인
SIGNIN_RESPONSE=$(curl -s -X POST "http://localhost:8000/v1/auth/signin" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "secure_password_123"
  }')

echo "로그인 응답: $SIGNIN_RESPONSE"

# 3. 토큰 추출 (jq 필요)
ACCESS_TOKEN=$(echo $SIGNIN_RESPONSE | jq -r '.access_token')
echo "Access Token: $ACCESS_TOKEN"

# 4. 사용자 정보 조회
ME_RESPONSE=$(curl -s -X GET "http://localhost:8000/v1/auth/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "사용자 정보: $ME_RESPONSE"

# 5. 로그아웃
SIGNOUT_RESPONSE=$(curl -s -X POST "http://localhost:8000/v1/auth/signout" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "로그아웃 응답: $SIGNOUT_RESPONSE"
```

---

## Python 테스트 코드 실행

### 1. 의존성 설치

```bash
# 가상환경 활성화
source venv/bin/activate

# 테스트 의존성 설치
pip install -r requirements.txt
```

### 2. 기본 테스트 실행 (엔드포인트 존재 확인)

```bash
# 모든 테스트 실행
pytest tests/test_auth.py -v

# 특정 테스트만 실행
pytest tests/test_auth.py::TestAuthAPI::test_signup_endpoint_exists -v

# 상세 출력과 함께 실행
pytest tests/test_auth.py -v -s
```

### 3. 실제 Supabase를 사용한 통합 테스트

실제 Supabase 연결이 필요한 테스트는 환경 변수가 설정되어 있을 때만 실행됩니다.

```bash
# .env 파일에 SUPABASE_URL과 SUPABASE_KEY 설정 필요

# 통합 테스트 실행
pytest tests/test_auth.py::TestAuthAPI::test_signup_success -v
pytest tests/test_auth.py::test_auth_flow_integration -v
```

### 4. 테스트 커버리지 확인

```bash
# pytest-cov 설치 (선택사항)
pip install pytest-cov

# 커버리지와 함께 실행
pytest tests/test_auth.py --cov=app.api.routes_auth --cov-report=html
```

---

## Postman/Thunder Client 사용

### 1. Postman Collection 생성

다음 JSON을 Postman에 import:

```json
{
  "info": {
    "name": "Auth API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "회원가입",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"email\": \"test@example.com\",\n  \"password\": \"test_password_123\"\n}"
        },
        "url": {
          "raw": "http://localhost:8000/v1/auth/signup",
          "host": ["localhost"],
          "port": "8000",
          "path": ["v1", "auth", "signup"]
        }
      }
    },
    {
      "name": "로그인",
      "event": [
        {
          "listen": "test",
          "script": {
            "exec": [
              "if (pm.response.code === 200) {",
              "    var jsonData = pm.response.json();",
              "    pm.environment.set(\"access_token\", jsonData.access_token);",
              "}"
            ]
          }
        }
      ],
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"email\": \"test@example.com\",\n  \"password\": \"test_password_123\"\n}"
        },
        "url": {
          "raw": "http://localhost:8000/v1/auth/signin",
          "host": ["localhost"],
          "port": "8000",
          "path": ["v1", "auth", "signin"]
        }
      }
    },
    {
      "name": "사용자 정보 조회",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{access_token}}"
          }
        ],
        "url": {
          "raw": "http://localhost:8000/v1/auth/me",
          "host": ["localhost"],
          "port": "8000",
          "path": ["v1", "auth", "me"]
        }
      }
    },
    {
      "name": "로그아웃",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{access_token}}"
          }
        ],
        "url": {
          "raw": "http://localhost:8000/v1/auth/signout",
          "host": ["localhost"],
          "port": "8000",
          "path": ["v1", "auth", "signout"]
        }
      }
    }
  ],
  "variable": [
    {
      "key": "access_token",
      "value": ""
    }
  ]
}
```

### 2. Thunder Client (VS Code Extension)

1. VS Code에서 Thunder Client 확장 설치
2. 새 요청 생성:
   - **회원가입**: POST `http://localhost:8000/v1/auth/signup`
   - **로그인**: POST `http://localhost:8000/v1/auth/signin`
   - **사용자 정보**: GET `http://localhost:8000/v1/auth/me` (Header에 `Authorization: Bearer <token>`)
   - **로그아웃**: POST `http://localhost:8000/v1/auth/signout` (Header에 `Authorization: Bearer <token>`)

---

## Swagger UI 사용

서버 실행 후 브라우저에서 다음 URL 접속:

```
http://localhost:8000/docs
```

Swagger UI에서:
1. 각 엔드포인트를 확인할 수 있습니다
2. "Try it out" 버튼으로 직접 테스트할 수 있습니다
3. 로그인 후 받은 토큰을 "Authorize" 버튼에서 설정할 수 있습니다

---

## 문제 해결

### 1. "ModuleNotFoundError: No module named 'fastapi'"

```bash
# 가상환경 활성화 확인
source venv/bin/activate

# 패키지 재설치
pip install -r requirements.txt
```

### 2. "SUPABASE_URL 환경 변수가 설정되지 않았습니다"

`.env` 파일이 프로젝트 루트에 있는지 확인하고, 다음 내용이 포함되어 있는지 확인:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

### 3. "401 Unauthorized" 오류

- 토큰이 만료되었을 수 있습니다. 다시 로그인하여 새 토큰을 받으세요
- Authorization 헤더 형식 확인: `Bearer <token>` (Bearer와 토큰 사이에 공백 필수)

### 4. "이미 등록된 이메일입니다"

테스트용으로 매번 다른 이메일을 사용하거나, Supabase 대시보드에서 사용자를 삭제하세요.

---

## 추가 리소스

- [Supabase Auth 문서](https://supabase.com/docs/guides/auth)
- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [pytest 문서](https://docs.pytest.org/)

