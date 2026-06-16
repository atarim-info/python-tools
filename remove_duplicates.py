#!/usr/bin/env python3
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

import csv
import os
import sys
import time
import argparse
import io

# Optional dependency: tqdm (progress bar). Fallback to no-progress iteration.
try:
    from tqdm import tqdm  # type: ignore
except ModuleNotFoundError:
    def tqdm(iterable, **kwargs):
        return iterable


def setup_utf8_stdout(errors='replace'):
    """
    Ensure stdout/stderr can encode non-ASCII characters (Hebrew, etc.) on Windows.
    """
    # stdout
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors=errors)
    except Exception:
        try:
            sys.stdout = io.TextIOWrapper(getattr(sys.stdout, 'buffer', sys.stdout),
                                           encoding='utf-8', errors=errors, line_buffering=True)
        except Exception:
            pass

    # stderr (important when exceptions are being formatted/printed)
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors=errors)
    except Exception:
        try:
            sys.stderr = io.TextIOWrapper(getattr(sys.stderr, 'buffer', sys.stderr),
                                            encoding='utf-8', errors=errors, line_buffering=True)
        except Exception:
            pass


def safe_text(value, encoding='utf-8', errors='replace'):
    """
    Convert value to text suitable for printing and file operations (Python 3 only).
    """
    try:
        if value is None:
            return ''
        if isinstance(value, str):
            return value
        if isinstance(value, (bytes, bytearray)):
            return bytes(value).decode(encoding, errors)
        return str(value)
    except Exception:
        return '[Unable to display path]'


def safe_print_path(label, path):
    """
    Print paths with Unicode characters (Python 3), forcing RTL display for Hebrew.

    Implementation:
    - Detect Hebrew/RTL characters
    - If present, render using python-bidi (get_display) so terminal shows correct RTL order
    """
    text = safe_text(path)

    # Hebrew is U+0590..U+05FF (and any character with bidi class R in practice).
    has_rtl = any(0x0590 <= ord(ch) <= 0x05FF for ch in text)

    if has_rtl:
        try:
            from bidi.algorithm import get_display  # type: ignore
            text = get_display(text)
        except Exception:
            # Fallback to raw text if python-bidi isn't available
            pass

    print(label + text)


def _is_probably_mojibake(s):
    # If the "╫" character exists, it strongly suggests mojibake from bad encoding.
    try:
        return '╫' in s
    except Exception:
        return False


def _hebrew_score(text):
    """
    Score decoded text by counting Hebrew characters (U+0590..U+05FF).
    Used to choose the most likely CSV decoding.
    """
    try:
        return sum(1 for ch in text if 0x0590 <= ord(ch) <= 0x05FF)
    except Exception:
        return 0


def repair_mojibake(text):
    """
    Attempt to reverse common mojibake patterns for Hebrew filenames.

    Returns the best candidate (based on Hebrew Unicode score),
    otherwise returns original `text`.
    """
    text = safe_text(text)
    if not _is_probably_mojibake(text):
        return text

    candidates = []
    try:
        candidates.append(('cp1255->utf-8', text.encode('cp1255', errors='replace').decode('utf-8', errors='replace')))
    except Exception:
        pass

    try:
        candidates.append(('latin1->utf-8', text.encode('latin1', errors='replace').decode('utf-8', errors='replace')))
    except Exception:
        pass

    try:
        candidates.append(('utf-8->cp1255', text.encode('utf-8', errors='replace').decode('cp1255', errors='replace')))
    except Exception:
        pass

    best = text
    best_score = _hebrew_score(text)

    for _, cand in candidates:
        score = _hebrew_score(cand)
        if score > best_score:
            best_score = score
            best = cand

    return best


def maybe_repair(text, repair_flag):
    if not repair_flag:
        return text
    try:
        return repair_mojibake(text)
    except Exception:
        return text


def parse_csv_report(csv_path, repair_flag=False):
    """Parse the duplicate report CSV and return duplicate file paths."""
    duplicates = []

    try:
        with open(csv_path, 'rb') as f:
            raw = f.read()
    except OSError as e:
        print('Error: Could not read CSV file {0}: {1}'.format(safe_text(csv_path), e))
        sys.exit(1)

    # Candidate encodings (common sources for Hebrew mojibake on Windows).
    # Note: If the CSV itself already contains mojibake "╫...", no reversible transform can recreate the original Hebrew reliably.
    candidates = [
        ('utf-8-sig', {'errors': 'strict'}),
        ('utf-16-le', {'errors': 'strict'}),
        ('cp1255', {'errors': 'strict'}),
        ('utf-8', {'errors': 'replace'}),
        ('latin1', {'errors': 'replace'}),
    ]

    best_decoded = None
    best_encoding = None
    best_score = -1

    for enc, opts in candidates:
        try:
            decoded = raw.decode(enc, **opts)
        except Exception:
            continue
        score = _hebrew_score(decoded)
        if score > best_score:
            best_score = score
            best_decoded = decoded
            best_encoding = enc

    if best_decoded is None:
        best_encoding = 'utf-8'
        best_decoded = raw.decode(best_encoding, errors='replace')

    # Avoid feeding pre-decoded text into csv (can trigger platform encoding issues).
    # Instead, let csv read from a TextIOWrapper over the raw bytes.
    text_stream = io.TextIOWrapper(io.BytesIO(raw), encoding=best_encoding, errors='replace', newline='')
    reader = csv.reader(text_stream)
    header_found = False

    for row in reader:
        if not row:
            continue

        if not header_found:
            normalized = [safe_text(cell).strip().lower() for cell in row]
            if normalized[:2] == ['original_path', 'duplicate_path']:
                header_found = True
            continue

        if len(row) < 2:
            continue

        original_path = safe_text(row[0]).strip()
        duplicate_path = safe_text(row[1]).strip()

        original_path = maybe_repair(original_path, repair_flag)
        duplicate_path = maybe_repair(duplicate_path, repair_flag)

        if duplicate_path:
            duplicates.append((original_path, duplicate_path))

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
        safe_print_path('Original:  ', original_path)
        safe_print_path('Duplicate: ', duplicate_path)
        print('')


def delete_duplicates(duplicates):
    """Delete duplicate files from the duplicate_path list."""
    deleted = []
    skipped = []

    for _, duplicate_path in tqdm(duplicates, desc="Deleting duplicates"):
        duplicate_path = safe_text(duplicate_path)

        if os.path.exists(duplicate_path):
            try:
                os.remove(duplicate_path)
                deleted.append(duplicate_path)
                safe_print_path('Deleted: ', duplicate_path)
            except OSError as e:
                skipped.append((duplicate_path, 'error', str(e)))
                print('Error deleting {0}: {1}'.format(safe_text(duplicate_path), e))
        else:
            skipped.append((duplicate_path, 'missing', 'File does not exist'))
            safe_print_path('Skipped missing file: ', duplicate_path)

    print('')
    print('Deletion summary:')
    print('  Deleted: {0}'.format(len(deleted)))
    print('  Skipped: {0}'.format(len(skipped)))

    return deleted, skipped


def confirm(prompt):
    """Ask user for confirmation."""
    answer = input(prompt)
    return answer.strip().lower() in ('y', 'yes')


def main():
    setup_utf8_stdout()
    parser = argparse.ArgumentParser(description='Remove duplicate files listed in a CSV report.')
    parser.add_argument('csv_report', help='Path to the duplicate CSV report')
    parser.add_argument('--delete', action='store_true', help='Delete duplicate files listed in the report')
    parser.add_argument('--repair-mojibake', action='store_true', help='Attempt to repair common Hebrew mojibake in the CSV paths')
    args = parser.parse_args()

    start_time = time.time()
    duplicates = parse_csv_report(args.csv_report, repair_flag=args.repair_mojibake)
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
