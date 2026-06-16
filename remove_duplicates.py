#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Duplicate remover utility.

Usage:
    python remove_duplicates.py <csv_report_path> [--delete]

The CSV should contain a header row with columns:
original_path,duplicate_path,size_bytes,hash

Without --delete, the script prints the candidates.
With --delete, it will remove duplicate_path files.
"""

from __future__ import print_function
import csv
import os
import sys
import time
import argparse
from tqdm import tqdm


def parse_csv_report(csv_path):
    """Parse the duplicate report CSV and return duplicate file paths."""
    duplicates = []

    try:
        with open(csv_path, 'r') as csvfile:
            reader = csv.reader(csvfile)
            header_found = False

            for row in reader:
                if not row:
                    continue

                if not header_found:
                    normalized = [cell.strip().lower() for cell in row]
                    if normalized[:2] == ['original_path', 'duplicate_path']:
                        header_found = True
                    continue

                if len(row) < 2:
                    continue

                original_path = row[0].strip()
                duplicate_path = row[1].strip()

                if duplicate_path:
                    duplicates.append((original_path, duplicate_path))
    except IOError as e:
        print('Error: Could not read CSV file {0}: {1}'.format(csv_path, e))
        sys.exit(1)

    return duplicates


def print_candidates(duplicates):
    """Print duplicate deletion candidates."""
    if not duplicates:
        print('No duplicate candidates found in CSV report.')
        return

    print('Duplicate deletion candidates:')
    print('Total candidates: {0}'.format(len(duplicates)))
    print('')

    for original_path, duplicate_path in duplicates:
        print('Original:  {0}'.format(original_path))
        print('Duplicate: {0}'.format(duplicate_path))
        print('')


def delete_duplicates(duplicates):
    """Delete duplicate files from the duplicate_path list."""
    deleted = []
    skipped = []

    for original_path, duplicate_path in tqdm(duplicates, desc="Deleting duplicates"):
        if os.path.exists(duplicate_path):
            try:
                os.remove(duplicate_path)
                deleted.append(duplicate_path)
                print('Deleted: {0}'.format(duplicate_path))
            except (OSError, IOError) as e:
                skipped.append((duplicate_path, 'error', str(e)))
                print('Error deleting {0}: {1}'.format(duplicate_path, e))
        else:
            skipped.append((duplicate_path, 'missing', 'File does not exist'))
            print('Skipped missing file: {0}'.format(duplicate_path))

    print('')
    print('Deletion summary:')
    print('  Deleted: {0}'.format(len(deleted)))
    print('  Skipped: {0}'.format(len(skipped)))

    return deleted, skipped


def confirm(prompt):
    """Ask user for confirmation."""
    try:
        answer = raw_input(prompt)
    except NameError:
        answer = input(prompt)
    return answer.strip().lower() in ('y', 'yes')


def main():
    parser = argparse.ArgumentParser(description='Remove duplicate files listed in a CSV report.')
    parser.add_argument('csv_report', help='Path to the duplicate CSV report')
    parser.add_argument('--delete', action='store_true', help='Delete duplicate files listed in the report')
    args = parser.parse_args()

    start_time = time.time()
    duplicates = parse_csv_report(args.csv_report)
    report_duration = time.time() - start_time

    if not duplicates:
        print('No duplicate deletion candidates found.')
        print('Report parsing time: {0:.2f} seconds'.format(report_duration))
        return

    print_candidates(duplicates)
    print('Report parsing time: {0:.2f} seconds'.format(report_duration))

    if not args.delete:
        print('Run with --delete to remove the duplicate files.')
        return

    if not confirm('Are you sure you want to permanently delete {0} files? [y/N]: '.format(len(duplicates))):
        print('Deletion cancelled.')
        return

    delete_start = time.time()
    delete_duplicates(duplicates)
    delete_duration = time.time() - delete_start
    print('Deletion time: {0:.2f} seconds'.format(delete_duration))


if __name__ == '__main__':
    main()
