#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Duplicate File Finder - Compare directories and find duplicate files

Usage:
    python duplicate_finder.py <directory1> <directory2>

Example:
    python duplicate_finder.py ./original ./backup
    
Compares files in both directories recursively and identifies duplicates.
Files from directory2 that are duplicates are marked as deletion candidates.
"""

from __future__ import print_function
import csv
import os
import sys
import time
import hashlib
import locale
from tqdm import tqdm


def format_seconds_to_hms(seconds):
    """
    Format seconds to H:m:s format.
    
    Args:
        seconds (float): Time in seconds
        
    Returns:
        str: Formatted time as H:m:s
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return "{0}:{1:02d}:{2:04.1f}".format(hours, minutes, secs)


def format_number_with_separator(number):
    """
    Format number with thousand separators according to locale.
    
    Args:
        number (int): Number to format
        
    Returns:
        str: Formatted number with commas
    """
    try:
        locale.setlocale(locale.LC_ALL, '')
        return locale.format_string("%d", number, grouping=True)
    except Exception:
        # Fallback to basic comma formatting
        return "{:,}".format(number)


def calculate_file_hash(filepath, blocksize=65536):
    """
    Calculate SHA256 hash of a file for content comparison.
    
    Args:
        filepath (str): Path to file
        blocksize (int): Block size for reading file
        
    Returns:
        str: SHA256 hash in hex format or None on error
    """
    try:
        sha256 = hashlib.sha256()
        # Ensure filepath is unicode on Python 2, str on Python 3
        if sys.version_info[0] < 3:
            if isinstance(filepath, str):
                try:
                    filepath = filepath.decode('utf-8')
                except (UnicodeDecodeError, AttributeError):
                    pass
        with open(filepath, 'rb') as f:
            buf = f.read(blocksize)
            while len(buf) > 0:
                sha256.update(buf)
                buf = f.read(blocksize)
        return sha256.hexdigest()
    except (IOError, OSError, UnicodeError) as e:
        try:
            filepath_display = filepath.encode('utf-8') if isinstance(filepath, type(u'')) else filepath
        except Exception:
            filepath_display = repr(filepath)
        print("  Warning: Could not hash {0}: {1}".format(filepath_display, e))
        return None


def build_file_index(directory):
    """
    Build an index of files in directory by size and hash.
    
    Args:
        directory (str): Path to directory to index
        
    Returns:
        tuple: (index, stats) where stats contains file and directory counts and duration
    """
    start_time = time.time()

    # Ensure directory path is unicode on Python 2
    if sys.version_info[0] < 3:
        if isinstance(directory, str):
            try:
                directory = directory.decode('utf-8')
            except (UnicodeDecodeError, AttributeError):
                pass

    if not os.path.isdir(directory):
        print("Error: Directory does not exist: {0}".format(directory))
        return {}, {'file_count': 0, 'dir_count': 0, 'error_count': 0, 'duration': 0.0}
    
    index = {}
    file_count = 0
    dir_count = 0
    error_count = 0
    
    print("Indexing directory: {0}".format(directory))
    
    for root, dirs, files in tqdm(os.walk(directory), desc="Scanning", unit=" dir"):
        dir_count += 1
        for filename in tqdm(files, desc="  Hashing", leave=False):
            filepath = os.path.join(root, filename)
            
            try:
                filesize = os.path.getsize(filepath)
                
                # Quick check by size first
                if filesize not in index:
                    index[filesize] = {}
                
                # Calculate hash for content comparison
                filehash = calculate_file_hash(filepath)
                if filehash is None:
                    error_count += 1
                    continue
                
                if filehash not in index[filesize]:
                    index[filesize][filehash] = []
                
                index[filesize][filehash].append(filepath)
                file_count += 1
                
            except (IOError, OSError, UnicodeError) as e:
                try:
                    filepath_display = filepath.encode('utf-8') if isinstance(filepath, type(u'')) else filepath
                except Exception:
                    filepath_display = repr(filepath)
                print("  Error processing {0}: {1}".format(filepath_display, e))
                error_count += 1
    
    duration = time.time() - start_time
    print("  Indexed {0} files in {1} directories ({2} errors) in {3:.2f} seconds\n".format(
        file_count, dir_count, error_count, duration))
    stats = {
        'file_count': file_count,
        'dir_count': dir_count,
        'error_count': error_count,
        'duration': duration
    }
    return index, stats


def find_duplicates(index1, index2):
    """
    Find files from index2 that are duplicates of files in index1.
    
    Args:
        index1 (dict): File index from directory 1
        index2 (dict): File index from directory 2
        
    Returns:
        dict: Duplicates found {size: {hash: [file_paths_in_dir2]}}
    """
    duplicates = {}
    
    # Check each file in index2 against index1
    for size in index2:
        if size in index1:
            for filehash in index2[size]:
                if filehash in index1[size]:
                    # This is a duplicate - files in dir2 are candidates for deletion
                    if size not in duplicates:
                        duplicates[size] = {}
                    duplicates[size][filehash] = index2[size][filehash]
    
    return duplicates


def generate_report(dir1, dir2, duplicates, index1, index2, stats1, stats2, compare_duration, total_duration):
    """
    Generate a detailed CSV report of duplicates and deletion candidates.
    
    Args:
        dir1 (str): First directory path
        dir2 (str): Second directory path
        duplicates (dict): Duplicates found
        index1 (dict): File index from directory 1
        index2 (dict): File index from directory 2
        stats1 (dict): Stats for directory 1 index
        stats2 (dict): Stats for directory 2 index
        compare_duration (float): Time spent comparing files
        
    Returns:
        list: Rows for CSV output
    """
    rows = []
    rows.append(["original_dir", dir1])
    rows.append(["duplicate_dir", dir2])
    rows.append([])
    rows.append(["files_indexed_dir1", stats1['file_count']])
    rows.append(["dirs_indexed_dir1", stats1['dir_count']])
    rows.append(["index_errors_dir1", stats1['error_count']])
    rows.append(["index_duration_dir1", format_seconds_to_hms(stats1['duration'])])
    rows.append([])
    rows.append(["files_indexed_dir2", stats2['file_count']])
    rows.append(["dirs_indexed_dir2", stats2['dir_count']])
    rows.append(["index_errors_dir2", stats2['error_count']])
    rows.append(["index_duration_dir2", format_seconds_to_hms(stats2['duration'])])
    rows.append([])
    rows.append(["compare_duration", format_seconds_to_hms(compare_duration)])
    rows.append(["total_duration", format_seconds_to_hms(total_duration)])
    rows.append([])
    rows.append(["duplicate_files_found", sum(len(hashes) for size in duplicates for hashes in duplicates[size].values())])
    rows.append(["duplicate_size_bytes", format_number_with_separator(sum(size * len(hashes) for size in duplicates for hashes in duplicates[size].values()))])
    rows.append([])
    rows.append(["original_path", "duplicate_path", "size_bytes", "hash"])

    if not duplicates:
        return rows
    
    for size in sorted(duplicates.keys()):
        for filehash in sorted(duplicates[size].keys()):
            orig_file = index1[size][filehash][0]
            for dup_file in sorted(duplicates[size][filehash]):
                rows.append([orig_file, dup_file, format_number_with_separator(size), filehash])
    
    return rows


def write_csv_report(report_rows, filename="duplicate_report.csv"):
    """Write CSV rows to a file."""
    # Ensure UTF-8 output across Python2 and Python3
    try:
        unicode_type = unicode  # noqa: F821 (Python2)
    except NameError:
        unicode_type = str

    def _encode_cell(cell):
        if isinstance(cell, unicode_type):
            if unicode_type is str:
                return cell
            return cell.encode('utf-8')
        return cell

    try:
        if sys.version_info[0] < 3:
            # Python 2: write bytes
            with open(filename, 'wb') as csvfile:
                writer = csv.writer(csvfile)
                for row in report_rows:
                    writer.writerow([_encode_cell(c) for c in row])
        else:
            # Python 3: write text with UTF-8 encoding
            with open(filename, 'w', encoding='utf-8', newline='') as csvfile:
                writer = csv.writer(csvfile)
                for row in report_rows:
                    writer.writerow([_encode_cell(c) for c in row])
        return True
    except IOError as e:
        print("Warning: Could not save CSV report: {0}".format(e))
        return False


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: python duplicate_finder.py <directory1> <directory2>")
        print("\nExample: python duplicate_finder.py ./original ./backup")
        print("\nFinds duplicate files and marks copies in directory2 as deletion candidates.")
        sys.exit(1)
    
    dir1 = sys.argv[1]
    dir2 = sys.argv[2]
    
    # Decode Unicode arguments on Python 2
    if sys.version_info[0] < 3:
        try:
            dir1 = dir1.decode('utf-8')
            dir2 = dir2.decode('utf-8')
        except (UnicodeDecodeError, AttributeError):
            pass
    
    print("Duplicate File Finder")
    print("=" * 70)
    print("")
    
    if not os.path.isdir(dir1) or not os.path.isdir(dir2):
        print("Error: One or both directories do not exist.")
        sys.exit(1)

    # Total timer (indexing + comparison)
    start_total = time.time()

    # Build indices for both directories
    index1, stats1 = build_file_index(dir1)
    index2, stats2 = build_file_index(dir2)
    
    # Find duplicates
    print("Comparing files...")
    start_compare = time.time()
    duplicates = find_duplicates(index1, index2)
    compare_duration = time.time() - start_compare
    print("  Comparison completed in {0:.2f} seconds\n".format(compare_duration))
    total_duration = time.time() - start_total
    print("Total elapsed time (indexing + comparison): {0:.2f} seconds\n".format(total_duration))
    
    # Generate report
    report_rows = generate_report(dir1, dir2, duplicates, index1, index2, stats1, stats2, compare_duration, total_duration)
    report_file = "duplicate_report.csv"
    if write_csv_report(report_rows, report_file):
        print("\nCSV report saved to: {0}".format(report_file))
    else:
        print("\nFailed to save CSV report.")


if __name__ == '__main__':
    main()
