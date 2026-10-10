# LIFE 2.0 API

MVP-1 member/action API. This service is intentionally separated from the existing `diagnosis-api Ver32.42`.

## Local
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8100
```

## Required env
Copy `.env.example`.

## Guardrails
- UNKNOWN is never converted to 0.
- Member FACT writes only happen through Action endpoints.
- AI never becomes the source of canonical FACT.
- Digital secrets are rejected.
- Existing diagnosis calculation logic is not copied here.
