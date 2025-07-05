#!/usr/bin/env python3
"""
Documentation Cleanup Analysis
Analyzes documentation files to identify which ones are actually needed for development.
"""

import os
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class DocumentationAnalyzer:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.docs_dir = self.root_dir / "docs"
        
        # Define essential documentation categories
        self.essential_docs = {
            "core_development": {
                "description": "개발에 핵심적으로 필요한 문서",
                "files": [
                    "architecture/database-schema.md",  # DB 스키마 - 개발시 필요
                    "guides/SETTINGS_REFERENCE.md",     # 환경변수 설정 - 개발시 필요
                    "guides/api-key-setup-guide.md",    # API 키 설정 - 개발시 필요
                ]
            },
            "operational": {
                "description": "운영/배포에 필요한 최소 문서",
                "files": [
                    "deployment/production-setup-guide.md",  # 프로덕션 설정
                    "security/SECURITY_CHECKLIST.md",        # 보안 체크리스트
                    "monitoring/MONITORING_GUIDE.md",        # 모니터링 가이드
                ]
            },
            "legacy_reference": {
                "description": "참고용으로만 필요한 문서 (보관)",
                "files": [
                    "architecture/CLEAN_ARCHITECTURE_GUIDE.md",  # 아키텍처 참고
                    "reports/PROJECT_STRUCTURE_REPORT.md",       # 프로젝트 구조 참고
                ]
            }
        }
        
        # Define unnecessary documentation (can be deleted)
        self.unnecessary_docs = {
            "outdated_reports": [
                "reports/CENTRAL_SYSTEM_ANALYSIS.md",
                "reports/DASHBOARD_COMPLETION_REPORT.md", 
                "reports/FINAL_PROJECT_SUMMARY.md",
                "reports/FINAL_SYSTEM_VERIFICATION.md",
                "reports/REFACTORING_COMPLETE.md",
                "reports/SYSTEM_REFACTORING_REPORT.md",
                "reports/SYSTEM_STATUS_REPORT.md",
                "reports/implementation-progress.md",
                "reports/phase6-completion-report.md"
            ],
            "planning_docs": [
                "roadmap/DANTARO_CENTRAL_ROADMAP.md",
                "roadmap/DASHBOARD_FIX_PLAN.md",
                "roadmap/DEVELOPMENT_PROGRESS.md",
                "roadmap/next-phase-roadmap.md",
                "roadmap/refactoring-plan.md"
            ],
            "development_tools": [
                "development/README_BADGES.md",
                "development/SPHINX_SETUP.md"
            ],
            "legacy_guides": [
                "legacy/FILE_COPY_CHECKLIST.md",
                "legacy/README_DOCS_INDEX.md",
                "legacy/websocket-integration-complete.md"
            ],
            "copilot_guides": [
                "guides/copilot-guide-central.md"  # AI가 사용하는 가이드 - 사람이 볼 필요 없음
            ],
            "detailed_architecture": [
                "architecture/exchange-modularization-completion.md",
                "architecture/websocket-design.md",
                "architecture/worker-architecture.md"
            ],
            "redundant_deployment": [
                "deployment/DEPLOYMENT_AUTOMATION.md",
                "deployment/DEPLOYMENT_GUIDE.md",
                "deployment/production-realtime-system.md"
            ],
            "testing_docs": [
                "testing/INTEGRATION_TEST_GUIDE.md",
                "testing/TEST_GUIDE.md"  # 테스트는 코드로 충분
            ],
            "performance_docs": [
                "monitoring/CACHE_OPTIMIZATION.md",
                "monitoring/PERFORMANCE_GUIDE.md",
                "monitoring/GRAFANA_DASHBOARD_SAMPLE.json"
            ],
            "extra_guides": [
                "guides/DANTARO_ENTERPRISE_GUIDE.md",
                "guides/ENTERPRISE_SETUP_GUIDE.md", 
                "guides/INTEGRATION_README.md",
                "guides/OPENAPI_USAGE.md"
            ],
            "security_extras": [
                "security/SECURITY_HARDENING.md"
            ]
        }
    
    def analyze_current_structure(self):
        """현재 문서 구조 분석"""
        print("📊 현재 문서 구조 분석")
        print("=" * 50)
        
        if not self.docs_dir.exists():
            print("❌ docs/ 디렉터리가 없습니다!")
            return {}
        
        structure = {}
        total_files = 0
        
        for category_dir in self.docs_dir.iterdir():
            if category_dir.is_dir():
                category = category_dir.name
                files = [f.name for f in category_dir.iterdir() if f.is_file() and f.name.endswith('.md') and f.name != 'README.md']
                structure[category] = files
                total_files += len(files)
                print(f"📁 {category}: {len(files)}개 파일")
        
        print(f"\n📊 총 {total_files}개 문서 파일")
        return structure
    
    def create_cleanup_plan(self):
        """정리 계획 생성"""
        print("\n🗂️ 문서 정리 계획")
        print("=" * 50)
        
        # Essential docs that should be kept
        essential_count = 0
        print("✅ 유지해야 할 핵심 문서:")
        for category, info in self.essential_docs.items():
            print(f"\n📂 {category} - {info['description']}")
            for file in info['files']:
                if (self.docs_dir / file).exists():
                    print(f"  ✅ {file}")
                    essential_count += 1
                else:
                    print(f"  ❌ {file} (파일 없음)")
        
        # Count unnecessary docs
        unnecessary_count = 0
        print(f"\n🗑️ 삭제할 수 있는 문서:")
        for category, files in self.unnecessary_docs.items():
            print(f"\n📂 {category}:")
            for file in files:
                file_path = self.docs_dir / file
                if file_path.exists():
                    print(f"  🗑️ {file}")
                    unnecessary_count += 1
                else:
                    print(f"  ➖ {file} (이미 없음)")
        
        print(f"\n📊 정리 요약:")
        print(f"  ✅ 유지: {essential_count}개 파일")
        print(f"  🗑️ 삭제 가능: {unnecessary_count}개 파일")
        
        return essential_count, unnecessary_count
    
    def generate_minimal_structure(self):
        """최소한의 문서 구조 제안"""
        print("\n🎯 제안하는 최소 문서 구조")
        print("=" * 50)
        
        minimal_structure = """
docs/
├── README.md (메인 인덱스)
├── setup/
│   ├── database-schema.md     # DB 스키마 (개발 필수)
│   ├── api-key-setup.md       # API 키 설정 (개발 필수)
│   └── environment-config.md  # 환경변수 설정 (개발 필수)
├── deployment/
│   ├── production-setup.md    # 프로덕션 배포
│   └── security-checklist.md  # 보안 체크리스트
└── reference/
    ├── architecture-guide.md  # 아키텍처 참고
    └── project-structure.md   # 프로젝트 구조 참고
"""
        print(minimal_structure)
        
        print("💡 이 구조의 장점:")
        print("  - 개발에 필요한 핵심 정보만 포함")
        print("  - 찾기 쉬운 간단한 구조")
        print("  - 유지보수 부담 최소화")
        print("  - AI가 참고하기에도 효율적")
    
    def create_cleanup_script(self):
        """정리 스크립트 생성"""
        cleanup_commands = []
        
        # Create backup command
        cleanup_commands.append("# 백업 생성")
        cleanup_commands.append("cp -r docs docs_full_backup")
        cleanup_commands.append("")
        
        # Delete unnecessary files
        cleanup_commands.append("# 불필요한 문서 삭제")
        for category, files in self.unnecessary_docs.items():
            cleanup_commands.append(f"# {category}")
            for file in files:
                file_path = self.docs_dir / file
                if file_path.exists():
                    cleanup_commands.append(f"rm -f docs/{file}")
        
        cleanup_commands.append("")
        cleanup_commands.append("# 빈 디렉터리 정리")
        cleanup_commands.append("find docs -type d -empty -delete")
        
        return "\n".join(cleanup_commands)

def main():
    """메인 함수"""
    root_dir = os.getcwd()
    analyzer = DocumentationAnalyzer(root_dir)
    
    print("🔍 Dantaro Central 문서 정리 분석")
    print("=" * 60)
    
    # 현재 구조 분석
    structure = analyzer.analyze_current_structure()
    
    # 정리 계획 생성
    essential_count, unnecessary_count = analyzer.create_cleanup_plan()
    
    # 최소 구조 제안
    analyzer.generate_minimal_structure()
    
    # 정리 스크립트 생성
    print("\n🛠️ 정리 스크립트 생성")
    print("=" * 50)
    cleanup_script = analyzer.create_cleanup_script()
    
    script_path = Path(root_dir) / "cleanup_docs.sh"
    with open(script_path, 'w') as f:
        f.write("#!/bin/bash\n")
        f.write("# Dantaro Central 문서 정리 스크립트\n\n")
        f.write(cleanup_script)
    
    os.chmod(script_path, 0o755)
    print(f"📄 정리 스크립트 생성: {script_path}")
    
    # 최종 요약
    print(f"\n🎉 분석 완료!")
    print(f"📊 현재: {essential_count + unnecessary_count}개 문서")
    print(f"🎯 정리 후: {essential_count}개 핵심 문서")
    print(f"💾 절약: {unnecessary_count}개 파일 ({(unnecessary_count/(essential_count + unnecessary_count)*100):.1f}% 감소)")
    
    print(f"\n🚀 다음 단계:")
    print(f"1. ./cleanup_docs.sh 실행하여 불필요한 문서 정리")
    print(f"2. 남은 핵심 문서들 내용 검토 및 업데이트")
    print(f"3. 새로운 docs/README.md 작성")

if __name__ == "__main__":
    main()
