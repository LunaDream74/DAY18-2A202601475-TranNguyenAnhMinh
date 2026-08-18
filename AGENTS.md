# Repository Guidelines

## Project Structure & Module Organization

This repository implements a staged production RAG lab in Python 3.11. Core code lives in `src/`: `m1_chunking.py` through `m5_enrichment.py` cover chunking, search, reranking, evaluation, and enrichment, while `pipeline.py` connects the stages. `main.py` compares the naive and production pipelines; `naive_baseline.py` records the starting baseline. Tests mirror the modules in `tests/test_m1.py` through `tests/test_m5.py`.

Use `data/` for the supplied Vietnamese source documents and `test_set.json` for evaluation cases. Store generated evaluation JSON under `reports/` (ignored by Git). Write analysis deliverables in `analysis/`, using the examples in `templates/`. Project-wide settings belong in `config.py`.

## Build, Test, and Development Commands

Create and activate a Python 3.11 virtual environment, then run:

```powershell
pip install -r requirements.txt
docker compose up -d
python naive_baseline.py
pytest tests/ -v
python src/pipeline.py
python main.py
python check_lab.py
```

Docker starts the local Qdrant service. Run the baseline before tuning the pipeline. `pytest` executes all module tests; a focused command such as `pytest tests/test_m2.py -v` is preferred while developing one stage. `check_lab.py` performs the final submission checks.

## Coding Style & Naming Conventions

Follow existing Python conventions: four-space indentation, type hints, concise docstrings, and imports grouped at the top of the file. Use `snake_case` for functions and variables, `PascalCase` for classes and dataclasses, and `UPPER_SNAKE_CASE` for constants in `config.py`. Keep module responsibilities aligned with the numbered pipeline stages. No formatter or linter is configured, so match nearby code and keep changes focused.

## Testing Guidelines

Tests use `pytest` and functions named `test_<behavior>`. Add tests to the file matching the changed module. Keep unit tests deterministic and avoid requiring live OpenAI or Qdrant services unless testing an integration path. There is no explicit coverage threshold; every behavior change should include a focused regression test, and the full suite must pass before submission.

## Commit & Pull Request Guidelines

Recent history uses Conventional Commit-style subjects such as `feat: ...` and `refactor: ...`. Continue with short, imperative messages (`fix: handle empty retrieval results`). Pull requests should summarize the affected pipeline stage, describe validation performed, link any relevant issue, and include before/after metrics or report excerpts when retrieval or evaluation behavior changes.

## Security & Configuration

Copy `.env.example` to `.env` and set `OPENAI_API_KEY` locally. Never commit `.env`, API keys, model credentials, or generated Qdrant data. Avoid committing large downloaded model artifacts or generated reports.
