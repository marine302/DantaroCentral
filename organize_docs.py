#!/usr/bin/env python3
"""
DantaroCentral 문서 정리 및 분류 스크립트
"""
import os
import shutil
from pathlib import Path
from datetime import datetime

def analyze_and_organize_docs():
    """문서들을 분석하고 정리"""
    project_root = Path(__file__).parent
    
    print("📚 DantaroCentral 문서 정리 시작...")
    
    # 현재 문서 상태 분석
    root_docs = []
    docs_folder_docs = []
    backend_docs = []
    archive_docs = []
    
    # 루트 디렉토리의 문서들
    for file in project_root.glob("*.md"):
        if file.name not in ['README.md', 'LICENSE']:
            root_docs.append(file.name)
    
    # docs 폴더의 문서들
    docs_dir = project_root / "docs"
    if docs_dir.exists():
        for file in docs_dir.glob("*.md"):
            docs_folder_docs.append(file.name)
        for file in docs_dir.glob("*.json"):
            docs_folder_docs.append(file.name)
    
    # backend/docs의 문서들
    backend_docs_dir = project_root / "backend" / "docs"
    if backend_docs_dir.exists():
        for file in backend_docs_dir.glob("*.md"):
            backend_docs.append(file.name)
    
    # backend/archive의 문서들
    archive_dir = project_root / "backend" / "archive"
    if archive_dir.exists():
        for file in archive_dir.glob("*.md"):
            archive_docs.append(file.name)
    
    print(f"📊 문서 현황:")
    print(f"  루트 디렉토리: {len(root_docs)}개")
    print(f"  docs/ 폴더: {len(docs_folder_docs)}개")
    print(f"  backend/docs/: {len(backend_docs)}개")
    print(f"  backend/archive/: {len(archive_docs)}개")
    
    # 문서 분류 정의
    doc_categories = {
        'current': {
            'description': '현재 활성 문서',
            'files': [
                'README.md',
                'PROJECT_STRUCTURE_REPORT.md',
                'CLEAN_ARCHITECTURE_GUIDE.md'
            ]
        },
        'api_guides': {
            'description': 'API 및 사용 가이드',
            'files': [
                'OPENAPI_USAGE.md',
                'api-key-setup-guide.md',
                'INTEGRATION_TEST_GUIDE.md',
                'TEST_GUIDE.md'
            ]
        },
        'architecture': {
            'description': '아키텍처 및 설계 문서',
            'files': [
                'database-schema.md',
                'worker-architecture.md',
                'websocket-design.md',
                'exchange-modularization-completion.md'
            ]
        },
        'deployment': {
            'description': '배포 및 운영',
            'files': [
                'DEPLOYMENT_GUIDE.md',
                'DEPLOYMENT_AUTOMATION.md',
                'production-setup-guide.md',
                'production-realtime-system.md',
                'MONITORING_GUIDE.md',
                'PERFORMANCE_GUIDE.md'
            ]
        },
        'security': {
            'description': '보안 및 설정',
            'files': [
                'SECURITY_CHECKLIST.md',
                'SECURITY_HARDENING.md',
                'SETTINGS_REFERENCE.md',
                'CACHE_OPTIMIZATION.md'
            ]
        },
        'legacy': {
            'description': '레거시/완료된 문서',
            'files': [
                'CENTRAL_SYSTEM_ANALYSIS.md',
                'DANTARO_CENTRAL_ROADMAP.md',
                'DANTARO_ENTERPRISE_GUIDE.md',
                'DASHBOARD_COMPLETION_REPORT.md',
                'DASHBOARD_FIX_PLAN.md',
                'DEVELOPMENT_PROGRESS.md',
                'ENTERPRISE_SETUP_GUIDE.md',
                'FILE_COPY_CHECKLIST.md',
                'FINAL_PROJECT_SUMMARY.md',
                'FINAL_SYSTEM_VERIFICATION.md',
                'INTEGRATION_README.md',
                'REFACTORING_COMPLETE.md',
                'SYSTEM_REFACTORING_REPORT.md',
                'SYSTEM_STATUS_REPORT.md',
                'implementation-progress.md',
                'next-phase-roadmap.md',
                'phase6-completion-report.md',
                'refactoring-plan.md',
                'websocket-integration-complete.md',
                'copilot-guide-central.md'
            ]
        },
        'tools': {
            'description': '도구 및 설정',
            'files': [
                'SPHINX_SETUP.md',
                'README_BADGES.md',
                'README_DOCS_INDEX.md',
                'GRAFANA_DASHBOARD_SAMPLE.json'
            ]
        }
    }
    
    return doc_categories, root_docs, docs_folder_docs, backend_docs, archive_docs

def reorganize_docs():
    """문서들을 새로운 구조로 재정리"""
    project_root = Path(__file__).parent
    
    # 새로운 docs 구조 생성
    new_docs_structure = {
        'docs/current': '현재 활성 문서',
        'docs/guides': 'API 및 사용 가이드', 
        'docs/architecture': '아키텍처 및 설계',
        'docs/deployment': '배포 및 운영',
        'docs/security': '보안 및 설정',
        'docs/legacy': '레거시/완료된 문서',
        'docs/tools': '도구 및 설정'
    }
    
    print("\n📁 새로운 문서 구조 생성 중...")
    
    for dir_path, description in new_docs_structure.items():
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✅ {dir_path} - {description}")
    
    # 문서 분류 및 이동
    doc_categories, root_docs, docs_folder_docs, backend_docs, archive_docs = analyze_and_organize_docs()
    
    moved_count = 0
    
    # 루트의 문서들을 적절한 위치로 이동
    for category, info in doc_categories.items():
        if category == 'current':
            continue  # 현재 활성 문서는 루트에 유지
            
        target_dir = project_root / 'docs' / (category if category != 'api_guides' else 'guides')
        
        for file_name in info['files']:
            source_file = project_root / file_name
            if source_file.exists():
                target_file = target_dir / file_name
                print(f"📦 이동: {file_name} → docs/{category}/")
                shutil.move(str(source_file), str(target_file))
                moved_count += 1
    
    # docs 폴더의 문서들도 재분류
    docs_dir = project_root / "docs"
    for file_name in docs_folder_docs:
        source_file = docs_dir / file_name
        if not source_file.exists():
            continue
            
        moved = False
        for category, info in doc_categories.items():
            if category == 'current':
                continue
                
            if file_name in info['files']:
                if category == 'api_guides':
                    target_dir = project_root / 'docs' / 'guides'
                else:
                    target_dir = project_root / 'docs' / category
                    
                target_file = target_dir / file_name
                if not target_file.exists():
                    print(f"📦 재정리: docs/{file_name} → docs/{category}/")
                    shutil.move(str(source_file), str(target_file))
                    moved_count += 1
                moved = True
                break
        
        # 분류되지 않은 파일들은 legacy로
        if not moved and source_file.exists():
            target_file = project_root / 'docs' / 'legacy' / file_name
            print(f"📦 레거시 이동: docs/{file_name} → docs/legacy/")
            shutil.move(str(source_file), str(target_file))
            moved_count += 1
    
    print(f"\n✅ 문서 재정리 완료! {moved_count}개 파일 이동됨")

def create_docs_index():
    """문서 인덱스 생성"""
    project_root = Path(__file__).parent
    
    docs_index_content = f"""# 📚 DantaroCentral 문서 인덱스

**최종 업데이트**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 🎯 현재 활성 문서 (프로젝트 루트)

| 문서 | 설명 | 상태 |
|------|------|------|
| [README.md](../README.md) | 메인 프로젝트 문서 | ✅ 최신 |
| [PROJECT_STRUCTURE_REPORT.md](../PROJECT_STRUCTURE_REPORT.md) | 프로젝트 구조 분석 보고서 | ✅ 최신 |
| [CLEAN_ARCHITECTURE_GUIDE.md](../CLEAN_ARCHITECTURE_GUIDE.md) | 클린 아키텍처 가이드 | ✅ 최신 |

## 📖 문서 카테고리

### 🔧 [가이드 문서](./guides/)
API 사용법, 테스트, 통합 가이드

### 🏗️ [아키텍처 문서](./architecture/)
시스템 설계, 데이터베이스 스키마, 모듈 구조

### 🚀 [배포 문서](./deployment/)
운영 환경 설정, 모니터링, 성능 최적화

### 🔒 [보안 문서](./security/)
보안 체크리스트, 설정 가이드, 캐시 최적화

### 🛠️ [도구 문서](./tools/)
개발 도구, 설정 파일, 템플릿

### 📦 [레거시 문서](./legacy/)
완료된 프로젝트, 이전 버전 문서

## 📋 문서 사용 가이드

### 🔍 **새로 시작하는 개발자**
1. [README.md](../README.md) - 프로젝트 개요
2. [guides/api-key-setup-guide.md](./guides/api-key-setup-guide.md) - API 키 설정
3. [deployment/production-setup-guide.md](./deployment/production-setup-guide.md) - 환경 구성

### 🏗️ **아키텍처 이해하기**
1. [PROJECT_STRUCTURE_REPORT.md](../PROJECT_STRUCTURE_REPORT.md) - 현재 구조
2. [architecture/database-schema.md](./architecture/database-schema.md) - DB 설계
3. [architecture/exchange-modularization-completion.md](./architecture/exchange-modularization-completion.md) - 모듈화 구조

### 🚀 **배포 및 운영**
1. [deployment/DEPLOYMENT_GUIDE.md](./deployment/DEPLOYMENT_GUIDE.md) - 배포 가이드
2. [deployment/MONITORING_GUIDE.md](./deployment/MONITORING_GUIDE.md) - 모니터링 설정
3. [security/SECURITY_CHECKLIST.md](./security/SECURITY_CHECKLIST.md) - 보안 체크

## 📊 문서 통계

- **총 문서 수**: 약 40개
- **현재 활성**: 3개
- **가이드 문서**: 4개
- **아키텍처 문서**: 4개
- **배포 문서**: 6개
- **보안 문서**: 4개
- **레거시 문서**: 18개
- **도구 문서**: 4개

## 🔄 문서 유지보수 규칙

1. **현재 문서**: 프로젝트 루트에 유지
2. **카테고리별 분류**: docs/ 하위 폴더로 구분
3. **레거시 처리**: 완료된 작업은 legacy 폴더로 이동
4. **정기 업데이트**: 프로젝트 변경시 관련 문서 업데이트

---
**관리자**: DantaroCentral Development Team
**구조 최적화 완료**: 2025-07-05
"""
    
    index_file = project_root / "docs" / "README.md"
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(docs_index_content)
    
    print("📝 docs/README.md 인덱스 파일 생성 완료")

def create_category_readmes():
    """각 카테고리별 README 생성"""
    project_root = Path(__file__).parent
    
    category_descriptions = {
        'guides': {
            'title': '📖 가이드 문서',
            'description': 'API 사용법, 테스트 방법, 통합 가이드 모음',
            'files': ['api-key-setup-guide.md', 'INTEGRATION_TEST_GUIDE.md', 'TEST_GUIDE.md', 'OPENAPI_USAGE.md']
        },
        'architecture': {
            'title': '🏗️ 아키텍처 문서', 
            'description': '시스템 설계, 데이터베이스 스키마, 모듈 구조 문서',
            'files': ['database-schema.md', 'worker-architecture.md', 'websocket-design.md', 'exchange-modularization-completion.md']
        },
        'deployment': {
            'title': '🚀 배포 및 운영',
            'description': '운영 환경 설정, 모니터링, 성능 최적화 가이드',
            'files': ['DEPLOYMENT_GUIDE.md', 'production-setup-guide.md', 'MONITORING_GUIDE.md', 'PERFORMANCE_GUIDE.md']
        },
        'security': {
            'title': '🔒 보안 문서',
            'description': '보안 체크리스트, 설정 가이드, 시스템 보안 강화',
            'files': ['SECURITY_CHECKLIST.md', 'SECURITY_HARDENING.md', 'SETTINGS_REFERENCE.md', 'CACHE_OPTIMIZATION.md']
        },
        'legacy': {
            'title': '📦 레거시 문서',
            'description': '완료된 프로젝트 단계, 이전 버전 문서 아카이브',
            'files': []  # 동적으로 생성
        },
        'tools': {
            'title': '🛠️ 도구 및 설정',
            'description': '개발 도구 설정, 템플릿, 유틸리티 문서',
            'files': ['SPHINX_SETUP.md', 'README_BADGES.md']
        }
    }
    
    for category, info in category_descriptions.items():
        category_dir = project_root / "docs" / category
        if not category_dir.exists():
            continue
            
        # 실제 파일 목록 가져오기
        actual_files = [f.name for f in category_dir.glob("*.md") if f.name != "README.md"]
        
        readme_content = f"""# {info['title']}

{info['description']}

## 📋 문서 목록

"""
        
        if actual_files:
            for file_name in sorted(actual_files):
                file_title = file_name.replace('.md', '').replace('-', ' ').replace('_', ' ').title()
                readme_content += f"- [{file_title}](./{file_name})\n"
        else:
            readme_content += "*현재 문서가 없습니다.*\n"
        
        readme_content += f"""
## 🔄 업데이트 정책

- 이 카테고리의 문서들은 프로젝트 발전에 따라 정기적으로 업데이트됩니다.
- 새로운 문서는 관련 기능 개발과 함께 추가됩니다.

---
**카테고리**: {info['title']}  
**최종 업데이트**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        
        readme_file = category_dir / "README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"📝 docs/{category}/README.md 생성 완료")

def update_main_readme():
    """메인 README.md에 문서 구조 정보 추가"""
    project_root = Path(__file__).parent
    main_readme = project_root / "README.md"
    
    if not main_readme.exists():
        return
    
    # README에 문서 섹션이 있는지 확인하고 업데이트
    with open(main_readme, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "## 📚 문서" not in content:
        docs_section = """
## 📚 문서

### 📖 문서 구조
- **[docs/](./docs/)** - 전체 문서 인덱스 및 카테고리별 문서
- **[PROJECT_STRUCTURE_REPORT.md](./PROJECT_STRUCTURE_REPORT.md)** - 프로젝트 구조 분석
- **[CLEAN_ARCHITECTURE_GUIDE.md](./CLEAN_ARCHITECTURE_GUIDE.md)** - 클린 아키텍처 가이드

### 🚀 빠른 시작
1. [API 키 설정](./docs/guides/api-key-setup-guide.md)
2. [배포 가이드](./docs/deployment/DEPLOYMENT_GUIDE.md)
3. [보안 체크리스트](./docs/security/SECURITY_CHECKLIST.md)

자세한 문서는 [docs/README.md](./docs/README.md)를 참조하세요.
"""
        
        # README 끝에 문서 섹션 추가
        updated_content = content + docs_section
        
        with open(main_readme, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print("📝 메인 README.md에 문서 섹션 추가 완료")

if __name__ == "__main__":
    print("📚 문서 정리 작업 시작...")
    
    reorganize_docs()
    create_docs_index()
    create_category_readmes()
    update_main_readme()
    
    print("\n🎉 문서 정리 완료!")
    print("📁 새로운 구조:")
    print("  ├── README.md (메인)")
    print("  ├── PROJECT_STRUCTURE_REPORT.md")
    print("  ├── CLEAN_ARCHITECTURE_GUIDE.md")
    print("  └── docs/")
    print("      ├── README.md (인덱스)")
    print("      ├── guides/ (가이드)")
    print("      ├── architecture/ (설계)")
    print("      ├── deployment/ (배포)")
    print("      ├── security/ (보안)")
    print("      ├── tools/ (도구)")
    print("      └── legacy/ (레거시)")
