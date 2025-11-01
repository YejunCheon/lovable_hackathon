# API 문서

이 문서는 AI Talent Search API의 주요 엔드포인트를 요약한 것입니다.

## 📚 완전한 API 문서

### 온라인 문서
서버 실행 후 다음 URL에서 대화형 API 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### API 스펙 파일
- **OpenAPI JSON**: `docs/openapi.json`
- **OpenAPI YAML**: `docs/openapi.yaml`
- **Postman Collection**: `docs/postman_collection.json`

이 파일들을 생성하려면:
```bash
python scripts/export_openapi.py
python scripts/generate_postman_collection.py
```

---

## 🚀 Base URL

- **Development**: `http://localhost:8000`
- **Production**: (설정 필요)

모든 API 엔드포인트는 `/v1` prefix를 사용합니다.

---

## 🔐 인증

대부분의 API는 인증이 필요합니다.

### 인증 방법

1. **로그인** 후 `access_token` 받기
2. 요청 헤더에 추가:
   ```
   Authorization: Bearer <access_token>
   ```

### 인증 엔드포인트

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| POST | `/v1/auth/signup` | 회원가입 |
| POST | `/v1/auth/signin` | 로그인 (이메일/비밀번호) |
| GET | `/v1/auth/oauth/google` | Google 소셜 로그인 |
| GET | `/v1/auth/oauth/linkedin` | LinkedIn 소셜 로그인 |
| GET | `/v1/auth/me` | 현재 사용자 정보 조회 |
| POST | `/v1/auth/signout` | 로그아웃 |

---

## 📋 주요 API 엔드포인트

### 1. 인증 (Authentication)

#### 회원가입
```http
POST /v1/auth/signup
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password_123"
}
```

#### 로그인
```http
POST /v1/auth/signin
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password_123"
}
```

**응답:**
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

#### 소셜 로그인 (Google)
```http
GET /v1/auth/oauth/google?redirect_to=http://localhost:3000/auth/callback
```

브라우저에서 접속하면 Google 로그인 페이지로 리다이렉트됩니다.

#### 현재 사용자 정보
```http
GET /v1/auth/me
Authorization: Bearer <access_token>
```

---

### 2. 검색 (Search)

#### 인재 검색
```http
POST /v1/search
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "query_text": "인공지능 전문가 찾기"
}
```

---

### 3. 후보자 (Candidates)

#### 벡터 생성
```http
POST /v1/candidates/generate-vectors
Authorization: Bearer <access_token>
```

---

## 📖 API 스펙 도구 사용법

### Swagger UI
1. 서버 실행: `uvicorn app.main:app --reload`
2. 브라우저에서 http://localhost:8000/docs 접속
3. 각 엔드포인트를 직접 테스트할 수 있습니다
4. "Authorize" 버튼을 클릭하여 토큰을 설정할 수 있습니다

### Postman
1. `docs/postman_collection.json` 파일을 Postman에 import
2. 환경 변수 설정:
   - `base_url`: `http://localhost:8000`
   - `access_token`: 로그인 후 받은 토큰
3. Collection의 요청을 실행하여 테스트

### Insomnia / Hoppscotch
1. `docs/openapi.json` 파일을 import
2. 서버 주소 설정
3. 인증 토큰 설정 후 사용

---

## 🔧 환경 변수

`.env` 파일에 다음 변수를 설정해야 합니다:

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
OAUTH_REDIRECT_URL=http://localhost:8000/v1/auth/callback

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_db
DB_USER=your_user
DB_PASSWORD=your_password

# Gemini API
GEMINI_API_KEY=your-gemini-key
```

---

## 📝 예제 코드

### JavaScript (fetch)
```javascript
// 로그인
const response = await fetch('http://localhost:8000/v1/auth/signin', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123'
  })
});

const data = await response.json();
const accessToken = data.access_token;

// 인증이 필요한 API 호출
const searchResponse = await fetch('http://localhost:8000/v1/search', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`
  },
  body: JSON.stringify({
    query_text: '인공지능 전문가 찾기'
  })
});
```

### Python (requests)
```python
import requests

BASE_URL = "http://localhost:8000"

# 로그인
login_response = requests.post(
    f"{BASE_URL}/v1/auth/signin",
    json={
        "email": "user@example.com",
        "password": "password123"
    }
)
access_token = login_response.json()["access_token"]

# 인증이 필요한 API 호출
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

search_response = requests.post(
    f"{BASE_URL}/v1/search",
    headers=headers,
    json={"query_text": "인공지능 전문가 찾기"}
)
```

---

## ⚠️ 주의사항

1. **토큰 만료**: Access token은 일정 시간 후 만료됩니다. 만료되면 다시 로그인해야 합니다.
2. **HTTPS**: 프로덕션 환경에서는 반드시 HTTPS를 사용하세요.
3. **에러 처리**: 모든 API는 에러 시 적절한 HTTP 상태 코드와 에러 메시지를 반환합니다.
4. **Rate Limiting**: 과도한 요청을 방지하기 위해 Rate Limiting이 적용될 수 있습니다.

---

## 📞 지원

문제가 발생하거나 질문이 있으시면:
- API 문서: http://localhost:8000/docs
- 테스트 가이드: `AUTH_API_TEST.md` 참고

---

**마지막 업데이트**: API 버전 0.1.0

