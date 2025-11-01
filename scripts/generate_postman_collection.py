#!/usr/bin/env python3
"""
Postman Collection을 생성하는 스크립트

사용법:
    python scripts/generate_postman_collection.py

생성되는 파일:
    - postman_collection.json: Postman Collection 파일
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.main import app

def generate_postman_collection():
    """OpenAPI 스펙을 기반으로 Postman Collection 생성"""
    
    # OpenAPI 스펙 가져오기
    openapi_schema = app.openapi()
    
    # Postman Collection 구조 생성
    collection = {
        "info": {
            "name": openapi_schema.get("info", {}).get("title", "API Collection"),
            "description": openapi_schema.get("info", {}).get("description", ""),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "_exporter_id": "api-talent-search"
        },
        "auth": {
            "type": "bearer",
            "bearer": [
                {
                    "key": "token",
                    "value": "{{access_token}}",
                    "type": "string"
                }
            ]
        },
        "variable": [
            {
                "key": "base_url",
                "value": "http://localhost:8000",
                "type": "string"
            },
            {
                "key": "access_token",
                "value": "",
                "type": "string"
            }
        ],
        "item": []
    }
    
    # OpenAPI 경로를 Postman 아이템으로 변환
    paths = openapi_schema.get("paths", {})
    
    for path, methods in paths.items():
        for method, details in methods.items():
            if method.lower() not in ["get", "post", "put", "delete", "patch"]:
                continue
            
            # 태그별로 그룹화
            tags = details.get("tags", ["Default"])
            tag = tags[0] if tags else "Default"
            
            # 태그별 폴더 찾기 또는 생성
            folder = None
            for item in collection["item"]:
                if item.get("name") == tag:
                    folder = item
                    break
            
            if folder is None:
                folder = {
                    "name": tag,
                    "item": []
                }
                collection["item"].append(folder)
            
            # 요청 생성
            request_item = {
                "name": details.get("summary") or details.get("operationId") or f"{method.upper()} {path}",
                "request": {
                    "method": method.upper(),
                    "header": [],
                    "url": {
                        "raw": "{{base_url}}" + path,
                        "host": ["{{base_url}}"],
                        "path": path.strip("/").split("/")
                    }
                },
                "response": []
            }
            
            # 설명 추가
            if details.get("description"):
                request_item["request"]["description"] = details.get("description")
            
            # Content-Type 헤더 추가 (POST, PUT, PATCH인 경우)
            if method.lower() in ["post", "put", "patch"]:
                request_item["request"]["header"].append({
                    "key": "Content-Type",
                    "value": "application/json"
                })
            
            # Authorization 헤더 추가 (security가 있는 경우)
            security = details.get("security", [])
            if security:
                request_item["request"]["auth"] = {
                    "type": "bearer",
                    "bearer": [
                        {
                            "key": "token",
                            "value": "{{access_token}}",
                            "type": "string"
                        }
                    ]
                }
            
            # 요청 본문 추가
            request_body = details.get("requestBody", {})
            if request_body:
                content = request_body.get("content", {})
                json_content = content.get("application/json", {})
                schema = json_content.get("schema", {})
                
                # 예시 생성 (스키마 기반)
                example = {}
                if "properties" in schema:
                    for prop_name, prop_schema in schema.get("properties", {}).items():
                        prop_type = prop_schema.get("type", "string")
                        if prop_type == "string":
                            example[prop_name] = f"example_{prop_name}"
                        elif prop_type == "integer":
                            example[prop_name] = 0
                        elif prop_type == "boolean":
                            example[prop_name] = False
                        else:
                            example[prop_name] = None
                
                request_item["request"]["body"] = {
                    "mode": "raw",
                    "raw": json.dumps(example, indent=2),
                    "options": {
                        "raw": {
                            "language": "json"
                        }
                    }
                }
            
            folder["item"].append(request_item)
    
    # 출력 디렉토리 생성
    output_dir = project_root / "docs"
    output_dir.mkdir(exist_ok=True)
    
    # 파일 저장
    collection_path = output_dir / "postman_collection.json"
    with open(collection_path, "w", encoding="utf-8") as f:
        json.dump(collection, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Postman Collection 생성 완료: {collection_path}")
    print(f"\n💡 사용 방법:")
    print(f"  1. Postman 열기")
    print(f"  2. Import > File 선택")
    print(f"  3. {collection_path.name} 파일 선택")
    print(f"  4. Collection에서 환경 변수 설정:")
    print(f"     - base_url: API 서버 주소")
    print(f"     - access_token: 로그인 후 받은 토큰")

if __name__ == "__main__":
    try:
        generate_postman_collection()
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

