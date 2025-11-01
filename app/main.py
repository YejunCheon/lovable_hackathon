from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes_search, routes_candidates, routes_auth
from app.adapters.pg import connect_db, close_db
import logging
import sys

app = FastAPI(
    title="AI Talent Search API",
    description="""
    AI Talent Search API - 인재 검색 및 인증 API
    
    ## 주요 기능
    
    ### 인증 (Authentication)
    - 회원가입 / 로그인 (이메일/비밀번호)
    - 소셜 로그인 (Google, LinkedIn)
    - JWT 토큰 기반 인증
    
    ### 검색 (Search)
    - 자연어 기반 인재 검색
    - AI 기반 Persona 생성
    
    ### 후보자 (Candidates)
    - 후보자 데이터 관리
    - 벡터 임베딩 생성
    
    ## Base URL
    - Development: `http://localhost:8000`
    - Production: (설정 필요)
    
    ## 인증 방법
    
    대부분의 엔드포인트는 인증이 필요합니다. 인증이 필요한 경우:
    1. `/v1/auth/signin` 또는 `/v1/auth/oauth/google`로 로그인
    2. 응답에서 받은 `access_token`을 사용
    3. 요청 헤더에 `Authorization: Bearer <access_token>` 추가
    """,
    version="0.1.0",
    contact={
        "name": "API Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
    },
)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 오리진 허용 (개발용)
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메소드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

app.include_router(routes_search.router, prefix="/v1")
app.include_router(routes_candidates.router, prefix="/v1")
app.include_router(routes_auth.router, prefix="/v1")

@app.on_event("startup")
async def startup_event():
    # 로깅 설정 (uvicorn이 이미 설정했을 수 있으므로 force=True 사용)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ],
        force=True  # 이미 설정되어 있어도 강제로 재설정
    )
    
    # app 네임스페이스의 로거들 레벨 설정
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.INFO)
    
    # uvicorn access 로그는 WARNING만 출력 (너무 많이 출력되므로)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    # 로깅 설정 확인
    logging.info("Logging configured successfully")
    
    await connect_db()

@app.on_event("shutdown")
async def shutdown_event():
    await close_db()

@app.get("/")
async def read_root():
    return {"message": "Welcome to the AI Talent Search API"}
