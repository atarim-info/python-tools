#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
File Sorter Utility - Sort files by year extracted from filename

Usage:
    python file_sorter.py [directory_path]

Example:
    python file_sorter.py ./photos
    
Files should have format: YYYY-MM-DD ... filename
Files will be organized into folders named by year.
"""

import os
import sys
import shutil
import re
import time


def extract_year(filename):
    """
    Extract year from filename.
    Assumes filename starts with YYYY-MM-DD format.
    
    Args:
        filename (str): Filename to parse
        
    Returns:
        str: Year (e.g., '2023') or None if not found
    """
    # Match YYYY pattern at the start of filename
    match = re.match(r'^(\d{4})', filename)
    if match:
        return match.group(1)
    return None


def sort_files_by_year(directory):
    """
    Sort files in directory into subdirectories by year.
    
    Args:
        directory (str): Path to directory containing files
        
    Returns:
        dict: Summary of operations performed
    """
    start_time = time.time()

    if not os.path.isdir(directory):
        print("Error: Directory does not exist: {0}".format(directory))
        return None
    
    summary = {
        'moved': 0,
        'skipped': 0,
        'errors': 0,
        'years': {},
        'scanned_items': 0,
        'scanned_files': 0,
        'scanned_directories': 0,
        'directories_created': 0,
        'duration': 0.0
    }
    
    # Get all files in directory
    try:
        items = os.listdir(directory)
    except OSError as e:
        print("Error: Unable to access directory: {0}\n  {1}".format(directory, e))
        summary['errors'] += 1
        summary['duration'] = time.time() - start_time
        return summary
    
    for item in tqdm(items, desc="Processing files"):
        summary['scanned_items'] += 1
        item_path = os.path.join(directory, item)
        
        # Skip if it's a directory
        if os.path.isdir(item_path):
            summary['scanned_directories'] += 1
            continue
        summary['scanned_files'] += 1
        
        # Extract year from filename
        year = extract_year(item)
        
        if year is None:
            print("Skipped: {0} (no year found)".format(item))
            summary['skipped'] += 1
            continue
        
        # Create year directory
        year_dir = os.path.join(directory, year)
        if not os.path.exists(year_dir):
            try:
                os.makedirs(year_dir)
                summary['directories_created'] += 1
                print("Created directory: {0}".format(year_dir))
            except OSError as e:
                print("Error creating directory {0}: {1}".format(year_dir, e))
                summary['errors'] += 1
                continue
        
        # Move file to year directory
        dest_path = os.path.join(year_dir, item)
        
        try:
            shutil.move(item_path, dest_path)
            print("Moved: {0} -> {1}/{2}".format(item, year, item))
            summary['moved'] += 1
            
            if year not in summary['years']:
                summary['years'][year] = 0
            summary['years'][year] += 1
            
        except (OSError, IOError) as e:
            print("Error moving file {0}: {1}".format(item, e))
            summary['errors'] += 1
    
    summary['duration'] = time.time() - start_time
    return summary


def print_summary(summary):
    """Print operation summary."""
    if summary is None:
        return

    print("\n" + "="*50)
    print("SORT SUMMARY")
    print("="*50)
    print("Files scanned:        {0}".format(summary['scanned_files']))
    print("Directories scanned:  {0}".format(summary['scanned_directories']))
    print("Directories created:  {0}".format(summary['directories_created']))
    print("Files moved:          {0}".format(summary['moved']))
    print("Files skipped:        {0}".format(summary['skipped']))
    print("Errors:               {0}".format(summary['errors']))
    print("Duration:             {0:.2f} seconds".format(summary['duration']))

    if summary['years']:
        print("\nFiles by year:")
        for year in sorted(summary['years'].keys()):
            print("  {0}: {1} file(s)".format(year, summary['years'][year]))

    print("="*50 + "\n")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python file_sorter.py <directory_path>")
        print("\nExample: python file_sorter.py ./photos")
        print("\nFiles will be sorted into subdirectories by year.")
        print("Assumes filenames start with YYYY-MM-DD format.")
        sys.exit(1)
    
    directory = sys.argv[1]
    
    print("Sorting files in: {0}".format(directory))
    print("-" * 50)
    
    summary = sort_files_by_year(directory)
    print_summary(summary)


if __name__ == '__main__':
    main()
