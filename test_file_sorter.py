#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for file_sorter utility.
Creates sample files and demonstrates the sorter.
"""

from __future__ import print_function
import os
import tempfile
import shutil
from file_sorter import sort_files_by_year, print_summary


def create_test_files(test_dir):
    """Create sample test files with various date formats."""
    test_files = [
        '2023-05-08 09.12.08.jpg',
        '2023-12-25 14.30.45.png',
        '2022-01-15 10.00.00.jpg',
        '2022-06-30 16.45.22.jpg',
        '2021-03-20 12.15.30.jpg',
        '2024-11-10 08.20.10.mp4',
        'no_date_file.jpg',  # This should be skipped
    ]
    
    for filename in test_files:
        filepath = os.path.join(test_dir, filename)
        # Create empty file
        with open(filepath, 'w') as f:
            f.write('test')
    
    print("Created test files in: {0}".format(test_dir))
    print("Files:")
    for f in test_files:
        print("  - {0}".format(f))
    print()


def main():
    """Run test."""
    # Create temporary directory for testing
    test_dir = tempfile.mkdtemp(prefix='file_sorter_test_')
    
    try:
        print("File Sorter Test")
        print("=" * 50)
        print()
        
        # Create test files
        create_test_files(test_dir)
        
        # Run sorter
        print("Running sorter...")
        print("-" * 50)
        summary = sort_files_by_year(test_dir)
        print_summary(summary)
        
        # Show results
        print("Final directory structure:")
        for root, dirs, files in os.walk(test_dir):
            level = root.replace(test_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            print("{0}{1}/".format(indent, os.path.basename(root) or 'root'))
            sub_indent = ' ' * 2 * (level + 1)
            for file in files:
                print("{0}{1}".format(sub_indent, file))
        
    finally:
        # Cleanup
        print("\nCleaning up test directory...")
        shutil.rmtree(test_dir)
        print("Done!")


if __name__ == '__main__':
    main()
