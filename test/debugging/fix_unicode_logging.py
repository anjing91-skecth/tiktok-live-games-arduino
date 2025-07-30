#!/usr/bin/env python3
"""
Fix Unicode Logging Errors
===========================
Script untuk mengganti emoji di logging dengan teks biasa agar tidak error di Windows console.
"""

import re
import os

def fix_emoji_in_file(file_path):
    """Replace emoji with text in logging messages"""
    
    emoji_replacements = {
        '📊': '[MEMORY]',
        '⚡': '[ARDUINO]',
        '🚀': '[SYSTEM]', 
        '📦': '[ARCHIVE]',
        '🎯': '[TARGET]',
        '🔍': '[MONITOR]',
        '🧹': '[CLEANUP]'
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Track changes
        changes_made = 0
        
        # Replace each emoji in logging messages
        for emoji, replacement in emoji_replacements.items():
            pattern = f'(logger\\.(?:info|debug|warning|error).*?){re.escape(emoji)}'
            if re.search(pattern, content):
                content = re.sub(pattern, f'\\1{replacement}', content)
                changes_made += 1
                print(f"  Replaced {emoji} with {replacement}")
        
        if changes_made > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed {changes_made} emoji logging messages in {file_path}")
        else:
            print(f"ℹ️ No emoji logging messages found in {file_path}")
            
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")

def main():
    """Fix emoji in all relevant files"""
    files_to_fix = [
        'src/core/unified_session_manager.py',
        'src/utils/memory_optimizer.py',
        'src/utils/statistics_optimizer.py'
    ]
    
    print("🔧 Fixing Unicode emoji in logging messages...")
    
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            print(f"\n📝 Processing {file_path}...")
            fix_emoji_in_file(file_path)
        else:
            print(f"⚠️ File not found: {file_path}")
    
    print("\n✅ Unicode logging fix completed!")

if __name__ == "__main__":
    main()
