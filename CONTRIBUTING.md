# Contributing

This started as a personal project, but issues and PRs are welcome.

## Setup

```bash
cp .env.example .env
cd infra && docker compose up -d
```

Backend (host-side, for running tests or editing outside Docker):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
pytest tests/unit
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Before opening a PR

- `pytest backend/tests/unit` passes
- `npm run build` succeeds in `frontend/`
- New agent logic gets a unit test with a mocked `ResearchState` (see
  `backend/tests/unit/test_writer.py` for the pattern)
- Pin new dependency versions exactly (`==x.y.z`, not `>=` or `^`) in
  `requirements.txt` / `package.json`
- No secrets or API keys in committed code — `.env` stays local, only
  `.env.example` (placeholders) gets committed

## Commit style

Conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`). Keep
commits scoped to one logical change.

## Reporting bugs

Open an issue with the query you ran, the agent/log output, and whether
you're on the local Ollama stack or a paid provider — search/LLM behavior
differs a lot between the two.
