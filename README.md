# Python 2.7.18 Project

This project contains various utilities for file organization and disk-space optimization —
including sorting, duplicate detection, reporting, and safe removal of duplicate files.

It is configured to use Python 2.7.18 via pyenv and includes file management utilities.

## Setup

The project uses pyenv to manage Python versions. Python 2.7.18 is specified in `.python-version`.

### Verify Python Version

```bash
pyenv versions
python --version
```

### Create and activate the virtual environment

```bash
pyenv install 2.7.18
pyenv local 2.7.18
virtualenv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### Running the utilities

Use the Python interpreter from the activated `.venv` or the `python` command after activating the environment.

#### Sort files by year

```bash
python file_sorter.py <directory_path>
```

- Moves files with names starting with `YYYY...` into year folders.
- Prints summary stats: scanned files, directories, moved files, skipped files, errors, and duration.

#### Find duplicate files

```bash
python duplicate_finder.py <directory1> <directory2>
```

- Recursively compares files in two directories.
- Generates `duplicate_report.csv` with index stats and duplicate candidates.

#### Remove duplicate files from a report

```bash
python remove_duplicates.py duplicate_report.csv [--delete]
```

- Prints duplicate deletion candidates from the CSV report.
- Use `--delete` to remove duplicates listed in `duplicate_path`.

## Configuration

- **Python Version**: 2.7.18
- **Version Manager**: pyenv
- **Virtual environment**: `.venv`
- **.python-version**: Pins Python 2.7.18 for the project
