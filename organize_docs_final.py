#!/usr/bin/env python3
"""
Dantaro Central Documentation Organizer
Comprehensive script to organize all documentation files into a clean, hierarchical structure.
"""

import os
import shutil
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class DocumentationOrganizer:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.docs_dir = self.root_dir / "docs"
        self.backup_dir = self.root_dir / "docs_backup"
        
        # Define the new documentation structure
        self.structure = {
            "architecture": {
                "description": "System architecture and design documentation",
                "files": [
                    "CLEAN_ARCHITECTURE_GUIDE.md",
                    "worker-architecture.md",
                    "websocket-design.md",
                    "exchange-modularization-completion.md",
                    "database-schema.md"
                ]
            },
            "guides": {
                "description": "Setup and usage guides",
                "files": [
                    "DANTARO_ENTERPRISE_GUIDE.md",
                    "ENTERPRISE_SETUP_GUIDE.md",
                    "INTEGRATION_README.md",
                    "api-key-setup-guide.md",
                    "copilot-guide-central.md",
                    "OPENAPI_USAGE.md",
                    "SETTINGS_REFERENCE.md"
                ]
            },
            "deployment": {
                "description": "Deployment and production guides",
                "files": [
                    "DEPLOYMENT_GUIDE.md",
                    "DEPLOYMENT_AUTOMATION.md",
                    "production-setup-guide.md",
                    "production-realtime-system.md"
                ]
            },
            "testing": {
                "description": "Testing documentation and guides",
                "files": [
                    "TEST_GUIDE.md",
                    "INTEGRATION_TEST_GUIDE.md"
                ]
            },
            "monitoring": {
                "description": "Monitoring and performance documentation",
                "files": [
                    "MONITORING_GUIDE.md",
                    "PERFORMANCE_GUIDE.md",
                    "CACHE_OPTIMIZATION.md",
                    "GRAFANA_DASHBOARD_SAMPLE.json"
                ]
            },
            "security": {
                "description": "Security documentation and checklists",
                "files": [
                    "SECURITY_CHECKLIST.md",
                    "SECURITY_HARDENING.md"
                ]
            },
            "development": {
                "description": "Development documentation and tools",
                "files": [
                    "SPHINX_SETUP.md",
                    "README_BADGES.md"
                ]
            },
            "reports": {
                "description": "Project reports and completion status",
                "files": [
                    "PROJECT_STRUCTURE_REPORT.md",
                    "SYSTEM_STATUS_REPORT.md",
                    "CENTRAL_SYSTEM_ANALYSIS.md",
                    "DASHBOARD_COMPLETION_REPORT.md",
                    "FINAL_PROJECT_SUMMARY.md",
                    "SYSTEM_REFACTORING_REPORT.md",
                    "REFACTORING_COMPLETE.md",
                    "FINAL_SYSTEM_VERIFICATION.md",
                    "phase6-completion-report.md",
                    "implementation-progress.md"
                ]
            },
            "roadmap": {
                "description": "Project roadmap and planning",
                "files": [
                    "DANTARO_CENTRAL_ROADMAP.md",
                    "next-phase-roadmap.md",
                    "DEVELOPMENT_PROGRESS.md",
                    "DASHBOARD_FIX_PLAN.md",
                    "refactoring-plan.md"
                ]
            },
            "legacy": {
                "description": "Legacy and archived documentation",
                "files": [
                    "FILE_COPY_CHECKLIST.md",
                    "websocket-integration-complete.md",
                    "README_DOCS_INDEX.md"
                ]
            }
        }
    
    def create_backup(self):
        """Create backup of existing docs structure"""
        if self.docs_dir.exists():
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)
            shutil.copytree(self.docs_dir, self.backup_dir)
            logger.info(f"Created backup at {self.backup_dir}")
    
    def create_structure(self):
        """Create the new directory structure"""
        # Remove existing docs directory
        if self.docs_dir.exists():
            shutil.rmtree(self.docs_dir)
        
        # Create new structure
        self.docs_dir.mkdir(exist_ok=True)
        
        for category, info in self.structure.items():
            category_dir = self.docs_dir / category
            category_dir.mkdir(exist_ok=True)
            logger.info(f"Created directory: {category_dir}")
    
    def move_files(self):
        """Move files to their appropriate directories"""
        moved_files = []
        missing_files = []
        
        for category, info in self.structure.items():
            category_dir = self.docs_dir / category
            
            for filename in info["files"]:
                # Look for file in root directory first
                source_file = self.root_dir / filename
                if not source_file.exists():
                    # Look in original docs directory (backup)
                    source_file = self.backup_dir / filename
                
                if source_file.exists():
                    dest_file = category_dir / filename
                    shutil.copy2(source_file, dest_file)
                    moved_files.append(f"{filename} -> {category}/")
                    logger.info(f"Moved {filename} to {category}/")
                else:
                    missing_files.append(filename)
                    logger.warning(f"File not found: {filename}")
        
        return moved_files, missing_files
    
    def create_category_readmes(self):
        """Create README.md files for each category"""
        for category, info in self.structure.items():
            category_dir = self.docs_dir / category
            readme_path = category_dir / "README.md"
            
            # Get list of files in the category
            files_in_category = [f for f in info["files"] if (category_dir / f).exists()]
            
            readme_content = f"""# {category.title()} Documentation

{info["description"]}

## Files in this category:

"""
            
            for filename in sorted(files_in_category):
                readme_content += f"- [{filename}](./{filename})\n"
            
            readme_content += f"""
---
*Generated by Dantaro Central Documentation Organizer*
"""
            
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            logger.info(f"Created README for {category}")
    
    def create_main_readme(self):
        """Create main documentation README"""
        readme_path = self.docs_dir / "README.md"
        
        readme_content = """# Dantaro Central Documentation

Welcome to the comprehensive documentation for Dantaro Central - a heavyweight central AI trading bot platform.

## Documentation Structure

This documentation is organized into the following categories:

"""
        
        for category, info in self.structure.items():
            files_count = len([f for f in info["files"] if (self.docs_dir / category / f).exists()])
            readme_content += f"### [{category.title()}](./{category}/)\n{info['description']}\n*({files_count} files)*\n\n"
        
        readme_content += """## Quick Links

### For Developers
- [Clean Architecture Guide](./architecture/CLEAN_ARCHITECTURE_GUIDE.md)
- [Worker Architecture](./architecture/worker-architecture.md)
- [Test Guide](./testing/TEST_GUIDE.md)

### For DevOps
- [Deployment Guide](./deployment/DEPLOYMENT_GUIDE.md)
- [Monitoring Guide](./monitoring/MONITORING_GUIDE.md)
- [Security Checklist](./security/SECURITY_CHECKLIST.md)

### For Users
- [Enterprise Guide](./guides/DANTARO_ENTERPRISE_GUIDE.md)
- [API Key Setup](./guides/api-key-setup-guide.md)
- [Integration README](./guides/INTEGRATION_README.md)

### Project Status
- [Project Structure Report](./reports/PROJECT_STRUCTURE_REPORT.md)
- [System Status Report](./reports/SYSTEM_STATUS_REPORT.md)
- [Final Project Summary](./reports/FINAL_PROJECT_SUMMARY.md)

---

## Contributing to Documentation

When adding new documentation:
1. Place files in the appropriate category directory
2. Update the category's README.md
3. Follow the established naming conventions
4. Use clear, descriptive titles and section headers

## Documentation Standards

- Use Markdown format for all documentation
- Include clear section headers
- Provide code examples where appropriate
- Keep documentation up-to-date with code changes
- Use consistent formatting and style

---
*Generated by Dantaro Central Documentation Organizer*
*Last updated: """ + str(self.root_dir) + """*
"""
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        logger.info("Created main documentation README")
    
    def cleanup_root_docs(self):
        """Remove organized documentation files from root directory"""
        removed_files = []
        
        for category, info in self.structure.items():
            for filename in info["files"]:
                root_file = self.root_dir / filename
                if root_file.exists():
                    root_file.unlink()
                    removed_files.append(filename)
                    logger.info(f"Removed {filename} from root directory")
        
        return removed_files
    
    def generate_report(self, moved_files, missing_files, removed_files):
        """Generate organization report"""
        report_path = self.root_dir / "DOCUMENTATION_ORGANIZATION_REPORT.md"
        
        report_content = f"""# Documentation Organization Report

## Summary
Successfully organized {len(moved_files)} documentation files into a structured hierarchy.

## New Structure
The documentation is now organized in the following structure:

```
docs/
├── README.md (main documentation index)
"""
        
        for category in self.structure.keys():
            files_count = len([f for f in self.structure[category]["files"] if (self.docs_dir / category / f).exists()])
            report_content += f"├── {category}/ ({files_count} files)\n"
            report_content += f"│   └── README.md\n"
        
        report_content += f"""```

## Files Moved ({len(moved_files)})
"""
        for file_move in sorted(moved_files):
            report_content += f"- {file_move}\n"
        
        if missing_files:
            report_content += f"""
## Missing Files ({len(missing_files)})
These files were referenced but not found:
"""
            for filename in sorted(missing_files):
                report_content += f"- {filename}\n"
        
        report_content += f"""
## Files Removed from Root ({len(removed_files)})
"""
        for filename in sorted(removed_files):
            report_content += f"- {filename}\n"
        
        report_content += """
## Benefits of New Structure
1. **Categorized**: Documents are logically grouped by purpose
2. **Discoverable**: Each category has its own README with file listings
3. **Maintainable**: Clear structure makes it easy to find and update docs
4. **Scalable**: Easy to add new categories or files as the project grows

## Next Steps
1. Review the organized documentation for accuracy
2. Update any cross-references between documents
3. Consider adding more detailed documentation where needed
4. Maintain the structure as new documentation is added

---
*Generated by Dantaro Central Documentation Organizer*
"""
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Generated organization report: {report_path}")
    
    def organize(self):
        """Main organization process"""
        logger.info("Starting documentation organization...")
        
        # Create backup
        self.create_backup()
        
        # Create new structure
        self.create_structure()
        
        # Move files
        moved_files, missing_files = self.move_files()
        
        # Create README files
        self.create_category_readmes()
        self.create_main_readme()
        
        # Clean up root directory
        removed_files = self.cleanup_root_docs()
        
        # Generate report
        self.generate_report(moved_files, missing_files, removed_files)
        
        logger.info(f"Documentation organization complete!")
        logger.info(f"Moved {len(moved_files)} files")
        logger.info(f"Missing {len(missing_files)} files")
        logger.info(f"Removed {len(removed_files)} files from root")
        
        return {
            "moved": len(moved_files),
            "missing": len(missing_files),
            "removed": len(removed_files)
        }

def main():
    """Main function"""
    import sys
    
    # Get project root directory
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = os.getcwd()
    
    # Initialize organizer
    organizer = DocumentationOrganizer(root_dir)
    
    # Run organization
    try:
        result = organizer.organize()
        print(f"\n✅ Documentation organization completed successfully!")
        print(f"📁 Moved: {result['moved']} files")
        print(f"⚠️  Missing: {result['missing']} files")
        print(f"🧹 Cleaned: {result['removed']} files from root")
        print(f"\n📚 Check the new structure in: {organizer.docs_dir}")
        print(f"📄 Full report: DOCUMENTATION_ORGANIZATION_REPORT.md")
        
    except Exception as e:
        logger.error(f"Error during organization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
