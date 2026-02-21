# AGENTS

## Project Goal

Maintain a playable color Tetris implementation in `tetris.py` using `pygame`.

## Environment

- Python version is pinned in `.python-version`.
- `direnv` is optional. Manual `venv` activation is always supported.
- Dependencies are in `requirements.txt`.

## Common Commands

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m py_compile tetris.py
python tetris.py
```

## Change Guidelines

- Keep gameplay logic clear and testable (`TetrisGame` class).
- Avoid adding heavy dependencies beyond `pygame`.
- Keep controls and run instructions in `README.md` up to date when behavior changes.
