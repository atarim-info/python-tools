#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for duplicate_finder utility.
Creates sample files and demonstrates the duplicate finder.
"""

from __future__ import print_function
import os
import tempfile
import shutil


def create_test_files():
    """Create test directory structure with duplicate files."""
    # Create temporary directories
    test_base = tempfile.mkdtemp(prefix='duplicate_finder_test_')
    dir1 = os.path.join(test_base, 'original')
    dir2 = os.path.join(test_base, 'backup')
    
    os.makedirs(dir1)
    os.makedirs(dir2)
    
    # Create test files in dir1
    test_files_dir1 = {
        'photo_2023_01.jpg': 'This is photo 1 from 2023',
        'photo_2023_02.jpg': 'This is photo 2 from 2023',
        'document.txt': 'This is an important document',
        'subdir/video.mp4': 'Video file content here',
    }
    
    for filename, content in test_files_dir1.items():
        filepath = os.path.join(dir1, filename)
        dirpath = os.path.dirname(filepath)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        with open(filepath, 'w') as f:
            f.write(content)
    
    # Create files in dir2 (some duplicates, some unique)
    test_files_dir2 = {
        'photo_2023_01.jpg': 'This is photo 1 from 2023',  # DUPLICATE
        'photo_2023_02.jpg': 'This is photo 2 from 2023',  # DUPLICATE
        'document.txt': 'This is an important document',   # DUPLICATE
        'subdir/video.mp4': 'Video file content here',     # DUPLICATE
        'unique_file.jpg': 'This file only exists in backup',
        'another_unique.txt': 'Another unique file',
    }
    
    for filename, content in test_files_dir2.items():
        filepath = os.path.join(dir2, filename)
        dirpath = os.path.dirname(filepath)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        with open(filepath, 'w') as f:
            f.write(content)
    
    return test_base, dir1, dir2


def main():
    """Run test."""
    test_base, dir1, dir2 = create_test_files()
    
    try:
        print("Duplicate Finder Test")
        print("=" * 70)
        print()
        print("Created test directories:")
        print("  {0}".format(dir1))
        print("  {0}".format(dir2))
        print()
        print("Test files created:")
        print("  4 files in original/")
        print("  6 files in backup/")
        print("  4 files are duplicates (same name and content)")
        print("  2 files are unique to backup/")
        print()
        
        # Import and run duplicate finder
        import sys
        sys.path.insert(0, '.')
        from duplicate_finder import build_file_index, find_duplicates, generate_report
        
        print("Running duplicate finder...")
        print("-" * 70)
        
        index1 = build_file_index(dir1)
        index2 = build_file_index(dir2)
        
        duplicates = find_duplicates(index1, index2)
        
        report = generate_report(dir1, dir2, duplicates, index1, index2)
        print(report)
        
    finally:
        # Cleanup
        print("\nCleaning up test directory...")
        shutil.rmtree(test_base)
        print("Done!")


if __name__ == '__main__':
    main()
