# Skills tutorial project

This repo teaches Claude Code skills. The skills in `.claude/skills/` are the working examples.

- Run skill scripts from the project root; sample inputs are in `data/`.
- After changing a skill or script: `python tools/skills_lint.py` and `python -m unittest discover -s tests`.
- Claude Code is started from a terminal with the venv `C:\pyenvsmy\claudeclioct26` activated, so `python` is the
  venv's Python. Skills call plain `python` and print JSON. Package skills (`analyzing-excel`, `plotting-charts`)
  list their packages in `scripts/requirements.txt`; install them into that venv, never into the system Python.
- Keep each skill description's "Not for ..." boundary as its last sentence (the tools in `tools/` rely on it).
