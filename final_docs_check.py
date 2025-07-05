#!/usr/bin/env python3
"""
Final Documentation Check Script
Verifies that all documentation is properly organized and accessible.
"""

import os
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def check_docs_structure():
    """Check the new documentation structure."""
    root_dir = Path(os.getcwd())
    docs_dir = root_dir / "docs"
    
    print("🔍 Checking Documentation Structure...")
    print("=" * 50)
    
    if not docs_dir.exists():
        print("❌ docs/ directory not found!")
        return False
    
    expected_categories = [
        "architecture",
        "guides", 
        "deployment",
        "testing",
        "monitoring",
        "security",
        "development",
        "reports",
        "roadmap",
        "legacy"
    ]
    
    print(f"📁 docs/ directory structure:")
    
    total_files = 0
    for category in expected_categories:
        category_dir = docs_dir / category
        if category_dir.exists():
            files = [f for f in category_dir.iterdir() if f.is_file() and f.name.endswith('.md')]
            total_files += len(files)
            print(f"  ├── {category}/ ({len(files)} files)")
            
            # Check if README exists
            readme_path = category_dir / "README.md"
            if readme_path.exists():
                print(f"  │   ├── ✅ README.md")
            else:
                print(f"  │   ├── ❌ README.md missing")
        else:
            print(f"  ├── ❌ {category}/ missing")
    
    # Check main README
    main_readme = docs_dir / "README.md"
    if main_readme.exists():
        print(f"  └── ✅ README.md (main)")
    else:
        print(f"  └── ❌ README.md (main) missing")
    
    print(f"\n📊 Total documentation files: {total_files}")
    return True

def check_root_cleanup():
    """Check that root directory is cleaned up."""
    root_dir = Path(os.getcwd())
    
    print("\n🧹 Checking Root Directory Cleanup...")
    print("=" * 50)
    
    # Files that should have been moved
    moved_files = [
        "CLEAN_ARCHITECTURE_GUIDE.md",
        "DANTARO_ENTERPRISE_GUIDE.md", 
        "PROJECT_STRUCTURE_REPORT.md",
        "SYSTEM_STATUS_REPORT.md",
        "DEPLOYMENT_GUIDE.md",
        "MONITORING_GUIDE.md"
    ]
    
    remaining_docs = []
    for filename in moved_files:
        if (root_dir / filename).exists():
            remaining_docs.append(filename)
    
    if remaining_docs:
        print("❌ Some documentation files still in root:")
        for filename in remaining_docs:
            print(f"  - {filename}")
        return False
    else:
        print("✅ Root directory cleaned successfully")
        return True

def check_key_files():
    """Check that key project files exist."""
    root_dir = Path(os.getcwd())
    
    print("\n🔑 Checking Key Project Files...")
    print("=" * 50)
    
    key_files = {
        "README.md": "Main project README",
        "backend/app/main.py": "Main application file",
        "backend/requirements.txt": "Python dependencies",
        "docs/README.md": "Main documentation index",
        "docs/guides/DANTARO_ENTERPRISE_GUIDE.md": "Enterprise guide",
        "docs/architecture/CLEAN_ARCHITECTURE_GUIDE.md": "Architecture guide",
        "DOCUMENTATION_ORGANIZATION_REPORT.md": "Organization report"
    }
    
    missing_files = []
    for filepath, description in key_files.items():
        full_path = root_dir / filepath
        if full_path.exists():
            print(f"✅ {filepath} - {description}")
        else:
            print(f"❌ {filepath} - {description}")
            missing_files.append(filepath)
    
    return len(missing_files) == 0

def check_backend_structure():
    """Check backend structure is clean."""
    root_dir = Path(os.getcwd())
    backend_dir = root_dir / "backend"
    
    print("\n🏗️ Checking Backend Structure...")
    print("=" * 50)
    
    if not backend_dir.exists():
        print("❌ backend/ directory not found!")
        return False
    
    # Check key backend directories
    key_dirs = {
        "app": "Main application code",
        "app/services": "Service modules", 
        "app/exchanges": "Exchange modules",
        "app/api": "API routes",
        "app/models": "Data models"
    }
    
    for dirname, description in key_dirs.items():
        dir_path = backend_dir / dirname
        if dir_path.exists():
            files_count = len([f for f in dir_path.iterdir() if f.is_file()])
            print(f"✅ {dirname}/ - {description} ({files_count} files)")
        else:
            print(f"❌ {dirname}/ - {description}")
    
    # Check for legacy files
    legacy_files = [
        "app/services/arbitrage_service.py",
        "app/services/old_market_service.py"
    ]
    
    legacy_found = []
    for filename in legacy_files:
        if (backend_dir / filename).exists():
            legacy_found.append(filename)
    
    if legacy_found:
        print("⚠️  Legacy files found:")
        for filename in legacy_found:
            print(f"  - {filename}")
    else:
        print("✅ No legacy files found")
    
    return True

def main():
    """Main check function."""
    print("🚀 Dantaro Central - Final Documentation Check")
    print("=" * 60)
    
    checks = [
        ("Documentation Structure", check_docs_structure),
        ("Root Directory Cleanup", check_root_cleanup), 
        ("Key Files", check_key_files),
        ("Backend Structure", check_backend_structure)
    ]
    
    results = {}
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"❌ Error in {check_name}: {e}")
            results[check_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 FINAL SUMMARY")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for check_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {check_name}")
    
    print(f"\n🎯 Overall Score: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All checks passed! Documentation is properly organized.")
        print("\n📚 Quick Links:")
        print(f"  - Main Documentation: docs/README.md")
        print(f"  - Enterprise Guide: docs/guides/DANTARO_ENTERPRISE_GUIDE.md")
        print(f"  - Architecture Guide: docs/architecture/CLEAN_ARCHITECTURE_GUIDE.md")
        print(f"  - Organization Report: DOCUMENTATION_ORGANIZATION_REPORT.md")
    else:
        print("⚠️  Some issues found. Please review and fix.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
