#!/usr/bin/env python3
"""
Smart Documentation Cleanup Script
Keeps only essential development documents and removes unnecessary files.
"""

import os
import shutil
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class SmartDocumentationCleaner:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.docs_dir = self.root_dir / "docs"
        self.archive_dir = self.root_dir / "docs_archive"
        
        # 개발에 필수적인 문서들 (6개)
        self.essential_docs = {
            "development": {
                "database-schema.md": "docs/architecture/database-schema.md",
                "environment-config.md": "docs/guides/SETTINGS_REFERENCE.md", 
                "api-key-setup.md": "docs/guides/api-key-setup-guide.md"
            },
            "deployment": {
                "production-setup.md": "docs/deployment/production-setup-guide.md"
            },
            "architecture": {
                "clean-architecture.md": "docs/architecture/CLEAN_ARCHITECTURE_GUIDE.md"
            },
            "security": {
                "security-checklist.md": "docs/security/SECURITY_CHECKLIST.md"
            }
        }
        
        # 참고용으로 보관할 문서들 (2개)
        self.reference_docs = {
            "project-structure-report.md": "docs/reports/PROJECT_STRUCTURE_REPORT.md",
            "monitoring-guide.md": "docs/monitoring/MONITORING_GUIDE.md"
        }
    
    def create_backup(self):
        """Create full backup before cleanup."""
        backup_dir = self.root_dir / "docs_full_backup"
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        shutil.copytree(self.docs_dir, backup_dir)
        logger.info(f"Created full backup at {backup_dir}")
    
    def create_new_structure(self):
        """Create the new minimal documentation structure."""
        # Remove existing docs
        if self.docs_dir.exists():
            shutil.rmtree(self.docs_dir)
        
        # Create new structure
        self.docs_dir.mkdir(exist_ok=True)
        
        # Create category directories
        for category in self.essential_docs.keys():
            (self.docs_dir / category).mkdir(exist_ok=True)
            logger.info(f"Created directory: docs/{category}/")
        
        # Create archive directory
        self.archive_dir.mkdir(exist_ok=True)
        logger.info(f"Created archive directory: {self.archive_dir}")
    
    def copy_essential_docs(self):
        """Copy essential documents to new structure."""
        backup_dir = self.root_dir / "docs_full_backup"
        copied_files = []
        missing_files = []
        
        for category, files in self.essential_docs.items():
            category_dir = self.docs_dir / category
            
            for new_name, old_path in files.items():
                # Try to find the file in backup
                source_file = backup_dir / old_path.replace("docs/", "")
                if not source_file.exists():
                    # Try root directory
                    source_file = self.root_dir / old_path.split("/")[-1]
                
                if source_file.exists():
                    dest_file = category_dir / new_name
                    shutil.copy2(source_file, dest_file)
                    copied_files.append(f"{new_name} -> {category}/")
                    logger.info(f"Copied {old_path} -> docs/{category}/{new_name}")
                else:
                    missing_files.append(old_path)
                    logger.warning(f"Missing file: {old_path}")
        
        return copied_files, missing_files
    
    def copy_reference_docs(self):
        """Copy reference documents to archive."""
        backup_dir = self.root_dir / "docs_full_backup"
        archived_files = []
        
        for new_name, old_path in self.reference_docs.items():
            source_file = backup_dir / old_path.replace("docs/", "")
            if not source_file.exists():
                source_file = self.root_dir / old_path.split("/")[-1]
            
            if source_file.exists():
                dest_file = self.archive_dir / new_name
                shutil.copy2(source_file, dest_file)
                archived_files.append(f"{new_name} -> archive/")
                logger.info(f"Archived {old_path} -> docs_archive/{new_name}")
        
        return archived_files
    
    def create_category_readmes(self):
        """Create README files for each category."""
        category_descriptions = {
            "development": "핵심 개발 문서",
            "deployment": "프로덕션 배포 가이드", 
            "architecture": "시스템 아키텍처",
            "security": "보안 체크리스트"
        }
        
        for category, description in category_descriptions.items():
            category_dir = self.docs_dir / category
            readme_path = category_dir / "README.md"
            
            # Get files in category
            files_in_category = [f.name for f in category_dir.iterdir() if f.is_file() and f.name.endswith('.md')]
            
            readme_content = f"""# {category.title()} Documentation

{description}

## Files:

"""
            for filename in sorted(files_in_category):
                readme_content += f"- [{filename}](./{filename})\n"
            
            readme_content += f"""
---
*Essential development documentation*
"""
            
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            logger.info(f"Created README for {category}")
    
    def create_main_readme(self):
        """Create main documentation README."""
        readme_path = self.docs_dir / "README.md"
        
        readme_content = """# Dantaro Central - Essential Documentation

이 문서들은 개발에 필수적인 핵심 정보만을 담고 있습니다.

## 📚 Documentation Structure

### [Development](./development/)
핵심 개발 문서 (3개)
- [Database Schema](./development/database-schema.md) - 데이터베이스 스키마
- [Environment Config](./development/environment-config.md) - 환경변수 설정
- [API Key Setup](./development/api-key-setup.md) - 거래소 API 키 설정

### [Deployment](./deployment/)
프로덕션 배포 (1개)
- [Production Setup](./deployment/production-setup.md) - 프로덕션 환경 설정

### [Architecture](./architecture/)
시스템 아키텍처 (1개)
- [Clean Architecture](./architecture/clean-architecture.md) - 시스템 전체 구조

### [Security](./security/)
보안 (1개)
- [Security Checklist](./security/security-checklist.md) - 보안 체크리스트

## 📦 Archive

참고용 문서는 `../docs_archive/` 디렉터리에 보관되어 있습니다.

## 🎯 Philosophy

**Less is More**: 개발에 정말 필요한 핵심 정보만 유지하여 빠른 참조와 쉬운 유지보수를 추구합니다.

---
*Generated by Smart Documentation Cleaner*
"""
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        logger.info("Created main documentation README")
    
    def generate_cleanup_report(self, copied_files, archived_files, missing_files):
        """Generate cleanup report."""
        backup_dir = self.root_dir / "docs_full_backup"
        
        # Count original files
        original_count = 0
        for root, dirs, files in os.walk(backup_dir):
            original_count += len([f for f in files if f.endswith('.md')])
        
        new_count = len(copied_files)
        archive_count = len(archived_files)
        reduction_percent = ((original_count - new_count) / original_count) * 100
        
        report_path = self.root_dir / "DOCUMENTATION_CLEANUP_REPORT.md"
        
        report_content = f"""# 📊 Documentation Cleanup Report

## Summary
Successfully reduced documentation from {original_count} files to {new_count} essential files.

## 🎯 New Structure (Essential Only)

```
docs/
├── README.md
├── development/ (3 files)
│   ├── database-schema.md
│   ├── environment-config.md
│   └── api-key-setup.md
├── deployment/ (1 file)
│   └── production-setup.md
├── architecture/ (1 file)
│   └── clean-architecture.md
└── security/ (1 file)
    └── security-checklist.md
```

## ✅ Essential Files Kept ({new_count})
"""
        
        for file_move in sorted(copied_files):
            report_content += f"- {file_move}\n"
        
        if archived_files:
            report_content += f"""
## 📦 Reference Files Archived ({archive_count})
"""
            for file_move in sorted(archived_files):
                report_content += f"- {file_move}\n"
        
        if missing_files:
            report_content += f"""
## ⚠️ Missing Files ({len(missing_files)})
"""
            for filename in sorted(missing_files):
                report_content += f"- {filename}\n"
        
        report_content += f"""
## 📊 Cleanup Statistics

- **Original files**: {original_count}
- **Essential files**: {new_count}  
- **Archived files**: {archive_count}
- **Reduction**: {reduction_percent:.1f}%
- **Files removed**: {original_count - new_count - archive_count}

## 🎯 Benefits

1. **Faster Reference**: Only 6 essential files to check
2. **Easier Maintenance**: Minimal files to update when code changes
3. **Better Focus**: No distraction from outdated reports or plans
4. **AI Efficiency**: Faster document parsing and reference

## 🔄 Backup

- **Full backup**: `docs_full_backup/` (can be deleted after verification)
- **Reference archive**: `docs_archive/` (keep for future reference)

---
*Generated by Smart Documentation Cleaner*
"""
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Generated cleanup report: {report_path}")
    
    def cleanup(self):
        """Main cleanup process."""
        logger.info("🚀 Starting smart documentation cleanup...")
        
        # Create backup
        self.create_backup()
        
        # Create new structure
        self.create_new_structure()
        
        # Copy essential documents
        copied_files, missing_files = self.copy_essential_docs()
        
        # Archive reference documents
        archived_files = self.copy_reference_docs()
        
        # Create README files
        self.create_category_readmes()
        self.create_main_readme()
        
        # Generate report
        self.generate_cleanup_report(copied_files, archived_files, missing_files)
        
        logger.info("✅ Smart documentation cleanup complete!")
        
        return {
            "essential": len(copied_files),
            "archived": len(archived_files),
            "missing": len(missing_files)
        }

def main():
    """Main function."""
    root_dir = os.getcwd()
    cleaner = SmartDocumentationCleaner(root_dir)
    
    try:
        result = cleaner.cleanup()
        
        print(f"\n🎉 Documentation cleanup completed!")
        print(f"✅ Essential files: {result['essential']}")
        print(f"📦 Archived files: {result['archived']}")
        print(f"⚠️  Missing files: {result['missing']}")
        
        print(f"\n📁 New structure:")
        print(f"  docs/ - {result['essential']} essential files")
        print(f"  docs_archive/ - {result['archived']} reference files")
        print(f"  docs_full_backup/ - complete backup")
        
        print(f"\n📄 Check: DOCUMENTATION_CLEANUP_REPORT.md")
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
