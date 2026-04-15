# FS25 Manager

FS25 Manager is a Python + PyQt6 desktop app for managing Farming Simulator 25 content on Linux.

It includes:
- local mod browsing and filtering
- savegame tools (backup/restore/new game creation)
- online mod browsing (Official, KINGMODS, FS25.NET)
- log analysis and radio settings utilities

## Table of Contents

- Overview
- Requirements
- Quick Start
- Development Setup
- Project Structure
- Testing
- Build and Packaging
- Release Workflow
- Troubleshooting
- Security and Reliability Notes

## Overview

Core entrypoint:
- `main.py` initializes Qt, validates/detects FS25 data path, and launches the main window.

Primary UI shell:
- `ui/main_window.py` hosts sidebar navigation and page routing.

Core service layer examples:
- `core/mod_manager.py`
- `core/save_manager.py`
- `core/fs25net_scraper.py`
- `core/kingmods_scraper.py`
- `core/log_analyzer.py`

## Requirements

- Linux desktop with Python 3.10+ (recommended 3.11+)
- `python3-venv` available
- Network access for online mod providers

Python dependencies (see `requirements.txt`):
- `PyQt6>=6.4.0`
- `Pillow`
- `requests`
- `beautifulsoup4`

## Quick Start

### Option 1: one-command run

```bash
./run.sh
```

`run.sh` auto-creates the virtual environment by calling `setup.sh` when needed.

### Option 2: manual setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
python main.py
```

## Development Setup

1. Create and activate virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -U pip
pip install -r requirements.txt
```

3. Run tests before changes and before pushing:

```bash
python -m pytest -q
```

4. Launch app for smoke check:

```bash
./run.sh
```

## Project Structure

```text
core/                 # business logic and integrations
ui/                   # PyQt pages, widgets, styles
tools/                # packaging helper binaries/assets
server-deploy/        # deploy artifacts and release metadata
server-deploy/releases/manifest.json
test_*.py             # unit/integration tests
main.py               # app entrypoint
FS25-Manager.spec     # PyInstaller spec
```

## Testing

Run full suite:

```bash
python -m pytest -q
```

Run a focused module:

```bash
python -m pytest test_save_manager_finalize.py -v
```

Current test strategy includes:
- core helpers and managers
- scraper fallback/error paths
- save creation and finalize edge cases
- UI helper utilities

## Build and Packaging

PyInstaller spec file:
- `FS25-Manager.spec`

Typical build command:

```bash
pyinstaller FS25-Manager.spec
```

Linux launcher setup helper:
- `setup.sh` creates a desktop entry in `~/.local/share/applications/fs25-manager.desktop`.

## Release Workflow

Recommended team workflow:

1. Use a dedicated feature/release branch (for example `4.11`, `4.12`).
2. Keep changes scoped and atomic.
3. Run full tests and a GUI smoke check (`./run.sh`).
4. Update release metadata when version changes:
	- `core/version.py`
	- `server-deploy/releases/manifest.json`
5. Push branch and open PR.

If shipping client artifacts:
- produce both Linux and Windows client builds
- place client release bundles under `server-deploy/releases`

## Troubleshooting

### App cannot find FS25 user data path

- App will prompt for manual folder selection.
- Choose the folder containing FS25 user files (mods/savegame folders).

### Missing dependencies or startup failures

```bash
source .venv/bin/activate
pip install -r requirements.txt
./run.sh
```

### Single-instance lock conflicts

- `main.py` uses `/tmp/mod_manager.lock`.
- If a stale lock remains after crash, close old process or remove the stale file.

## Security and Reliability Notes

- Network operations are wrapped with defensive fallbacks where possible.
- Scraper and download operations use worker threads to keep UI responsive.
- Error handling is designed to avoid crashes on partial network/service failures.
- Tests should be kept green before every push.

## License

No license file is currently present in this repository.
If this project is intended for public distribution, add a `LICENSE` file and update this section.

