#!/bin/bash
# Dantaro Central 문서 정리 스크립트

# 백업 생성
cp -r docs docs_full_backup

# 불필요한 문서 삭제
# outdated_reports
rm -f docs/reports/CENTRAL_SYSTEM_ANALYSIS.md
rm -f docs/reports/DASHBOARD_COMPLETION_REPORT.md
rm -f docs/reports/FINAL_PROJECT_SUMMARY.md
rm -f docs/reports/FINAL_SYSTEM_VERIFICATION.md
rm -f docs/reports/REFACTORING_COMPLETE.md
rm -f docs/reports/SYSTEM_REFACTORING_REPORT.md
rm -f docs/reports/SYSTEM_STATUS_REPORT.md
rm -f docs/reports/implementation-progress.md
rm -f docs/reports/phase6-completion-report.md
# planning_docs
rm -f docs/roadmap/DANTARO_CENTRAL_ROADMAP.md
rm -f docs/roadmap/DASHBOARD_FIX_PLAN.md
rm -f docs/roadmap/DEVELOPMENT_PROGRESS.md
rm -f docs/roadmap/next-phase-roadmap.md
rm -f docs/roadmap/refactoring-plan.md
# development_tools
rm -f docs/development/README_BADGES.md
rm -f docs/development/SPHINX_SETUP.md
# legacy_guides
rm -f docs/legacy/FILE_COPY_CHECKLIST.md
rm -f docs/legacy/README_DOCS_INDEX.md
rm -f docs/legacy/websocket-integration-complete.md
# copilot_guides
rm -f docs/guides/copilot-guide-central.md
# detailed_architecture
rm -f docs/architecture/exchange-modularization-completion.md
rm -f docs/architecture/websocket-design.md
rm -f docs/architecture/worker-architecture.md
# redundant_deployment
rm -f docs/deployment/DEPLOYMENT_AUTOMATION.md
rm -f docs/deployment/DEPLOYMENT_GUIDE.md
rm -f docs/deployment/production-realtime-system.md
# testing_docs
rm -f docs/testing/INTEGRATION_TEST_GUIDE.md
rm -f docs/testing/TEST_GUIDE.md
# performance_docs
rm -f docs/monitoring/CACHE_OPTIMIZATION.md
rm -f docs/monitoring/PERFORMANCE_GUIDE.md
rm -f docs/monitoring/GRAFANA_DASHBOARD_SAMPLE.json
# extra_guides
rm -f docs/guides/DANTARO_ENTERPRISE_GUIDE.md
rm -f docs/guides/ENTERPRISE_SETUP_GUIDE.md
rm -f docs/guides/INTEGRATION_README.md
rm -f docs/guides/OPENAPI_USAGE.md
# security_extras
rm -f docs/security/SECURITY_HARDENING.md

# 빈 디렉터리 정리
find docs -type d -empty -delete