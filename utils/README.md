# Python Tools Project (Python 3.12+)

This project contains various utilities for file organization and disk-space optimization —
including sorting, duplicate detection, reporting, and safe removal of duplicate files.

## Python version

The project pins Python version via `.python-version`.

### Verify Python Version

```bash
python --version
```

## Setup

Create and activate the virtual environment (example):

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the utilities

Use the Python interpreter from the activated `.venv` (recommended) to run the scripts.

### Sort files by year

```bash
python file_sorter.py <directory_path>
```

- Moves files into year folders based on filename patterns:
  - `YYYY...` (e.g. `2023-05-08 ...`)
  - `IMG_YYYYMMDD_...` (e.g. `IMG_20160326_171252.jpg`)
  - `C360_YYYY-MM-DD-...` (e.g. `C360_2015-12-26-17-29-01-627.jpg`)
  - `PANO_YYYYMMDD_...` (e.g. `PANO_20151116_163437.jpg`)
- Prints summary stats: scanned files, directories, moved files, skipped files, errors, and duration.

### Find duplicate files

```bash
python duplicate_finder.py <directory1> <directory2>
```

- Recursively compares files in two directories.
- Generates `duplicate_report.csv` with index stats and duplicate candidates.

### Remove duplicate files from a report

```bash
python remove_duplicates.py duplicate_report.csv [--delete] [--repair-mojibake]
```

- Prints duplicate deletion candidates from the CSV report.
- Use `--delete` to remove duplicates listed in `duplicate_path`.
- Use `--repair-mojibake` to attempt fixing common Hebrew mojibake in paths.
- Hebrew/RTL filenames are displayed using `python-bidi` (best-effort for console rendering).

## Configuration

- **Python Version**: see `.python-version` (tested with Python 3.12+)
- **Virtual environment**: `.venv`
- **Dependencies**: installed via `requirements.txt`
python file_sorter.py <directory_path>
.venv\Scripts\activate
python --version
