#!/bin/bash
# Final cleanup of temporary analysis and organization scripts
# These scripts were created for one-time documentation organization tasks

echo "🧹 Final cleanup of temporary scripts..."

# Remove temporary documentation organization scripts
temporary_scripts=(
    "analyze_docs.py"
    "cleanup_docs.py" 
    "cleanup_root_docs.sh"
    "organize_docs_final.py"
    "organize_docs.py"
    "cleanup_docs.sh"
    "check_root_docs.py"
    "final_docs_check.py"
)

for script in "${temporary_scripts[@]}"; do
    if [ -f "$script" ]; then
        echo "🗑️ Removing temporary script: $script"
        rm "$script"
    fi
done

# Keep these scripts as they might be useful for future maintenance
echo "✅ Keeping useful scripts:"
echo "  📜 cleanup_project.py - General project cleanup"
echo "  📜 cleanup_modular_exchanges.py - Exchange module cleanup"

echo ""
echo "✅ Root directory cleanup complete!"
echo "📊 Removed temporary documentation organization scripts"
echo "🎯 Root directory now contains only essential files"
