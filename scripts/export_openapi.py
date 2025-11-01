#!/usr/bin/env python3
"""
OpenAPI 스펙 파일을 생성하는 스크립트

사용법:
    python scripts/export_openapi.py

생성되는 파일:
    - openapi.json: OpenAPI 3.0 JSON 스펙
    - openapi.yaml: OpenAPI 3.0 YAML 스펙
"""
import json
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.main import app
import yaml

def export_openapi():
    """OpenAPI 스펙을 JSON과 YAML 형식으로 내보내기"""
    
    # OpenAPI 스펙 가져오기
    openapi_schema = app.openapi()
    
    # 출력 디렉토리 생성
    output_dir = project_root / "docs"
    output_dir.mkdir(exist_ok=True)
    
    # JSON 형식으로 저장
    json_path = output_dir / "openapi.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)
    print(f"✅ OpenAPI JSON 생성 완료: {json_path}")
    
    # YAML 형식으로 저장
    yaml_path = output_dir / "openapi.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(openapi_schema, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    print(f"✅ OpenAPI YAML 생성 완료: {yaml_path}")
    
    print(f"\n📄 생성된 파일:")
    print(f"  - {json_path.relative_to(project_root)}")
    print(f"  - {yaml_path.relative_to(project_root)}")
    print(f"\n💡 사용 방법:")
    print(f"  - Postman: Import > File > openapi.json 선택")
    print(f"  - Insomnia: Import > From File > openapi.json 선택")
    print(f"  - Swagger Editor: https://editor.swagger.io/ 에서 openapi.yaml 열기")
    print(f"  - Redoc: https://redocly.github.io/redoc/ 에서 openapi.yaml 열기")

if __name__ == "__main__":
    try:
        export_openapi()
    except ImportError as e:
        print(f"❌ 오류: PyYAML이 설치되지 않았습니다.")
        print(f"   설치 방법: pip install pyyaml")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

