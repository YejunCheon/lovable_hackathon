# AI Talent Search API

AI 기반 인재 검색 플랫폼의 백엔드 API입니다.

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 또는
venv\Scripts\activate  # Windows

# 패키지 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 프로젝트 루트에 생성하고 다음 내용을 추가하세요:

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

### 3. 서버 실행

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. API 문서 확인

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📚 API 문서

### 온라인 문서 (서버 실행 필요)
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 파일 기반 문서
- `API_DOCS.md` - API 개요 및 주요 엔드포인트
- `AUTH_API_TEST.md` - 인증 API 상세 테스트 가이드

### API 스펙 파일 생성

FE 개발자를 위해 OpenAPI 스펙과 Postman Collection을 생성할 수 있습니다:

```bash
# OpenAPI JSON/YAML 생성
python scripts/export_openapi.py

# Postman Collection 생성
python scripts/generate_postman_collection.py
```

생성된 파일은 `docs/` 디렉토리에 저장됩니다:
- `docs/openapi.json` - OpenAPI 3.0 JSON 스펙
- `docs/openapi.yaml` - OpenAPI 3.0 YAML 스펙
- `docs/postman_collection.json` - Postman Collection

---

## 🛠️ 개발

### 테스트 실행

```bash
# 모든 테스트 실행
pytest tests/ -v

# 특정 테스트만 실행
pytest tests/test_auth.py -v

# 커버리지와 함께 실행
pytest tests/ --cov=app --cov-report=html
```

### 코드 포맷팅

```bash
# Black (코드 포맷터)
black app/ tests/

# isort (import 정렬)
isort app/ tests/
```

---

## 📁 프로젝트 구조

```
.
├── app/
│   ├── api/              # API 라우트
│   ├── adapters/         # 외부 서비스 어댑터
│   ├── core/             # 핵심 설정
│   ├── schemas/          # Pydantic 스키마
│   ├── services/         # 비즈니스 로직
│   └── utils/            # 유틸리티
├── scripts/              # 유틸리티 스크립트
├── tests/                # 테스트 코드
├── docs/                 # 생성된 API 스펙 파일
├── app/main.py           # FastAPI 애플리케이션
└── requirements.txt      # Python 의존성
```

---

## 🔐 인증

API는 JWT 토큰 기반 인증을 사용합니다.

1. `/v1/auth/signin` 또는 소셜 로그인으로 로그인
2. 응답에서 `access_token` 받기
3. 요청 헤더에 `Authorization: Bearer <access_token>` 추가

자세한 내용은 `AUTH_API_TEST.md`를 참고하세요.

---

## 📖 FE 개발자를 위한 가이드

### 1. API 스펙 확인

서버 실행 후 http://localhost:8000/docs 에서 Swagger UI를 확인하세요.

### 2. Postman Collection 사용

1. `python scripts/generate_postman_collection.py` 실행
2. Postman에서 `docs/postman_collection.json` import
3. 환경 변수 설정:
   - `base_url`: `http://localhost:8000`
   - `access_token`: 로그인 후 받은 토큰

### 3. OpenAPI 스펙 사용

다양한 도구에서 OpenAPI 스펙을 사용할 수 있습니다:

- **Swagger Editor**: https://editor.swagger.io/
- **Redoc**: https://redocly.github.io/redoc/
- **Insomnia**: File > Import > OpenAPI
- **Postman**: Import > File > OpenAPI

### 4. 예제 코드

JavaScript, Python 예제는 `API_DOCS.md`를 참고하세요.

---

## 🐛 문제 해결

### ImportError 발생 시

```bash
# 가상환경이 활성화되었는지 확인
which python3  # venv/bin/python3를 가리켜야 함

# 패키지 재설치
pip install -r requirements.txt
```

### Supabase 연결 오류

`.env` 파일의 `SUPABASE_URL`과 `SUPABASE_KEY`가 올바른지 확인하세요.

### 데이터베이스 연결 오류

PostgreSQL이 실행 중인지 확인하고, `.env` 파일의 데이터베이스 설정을 확인하세요.

---

## 📝 라이센스

MIT

---

## 📞 지원

문제가 발생하거나 질문이 있으시면:
- API 문서: http://localhost:8000/docs
- 테스트 가이드: `AUTH_API_TEST.md`

