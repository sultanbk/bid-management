# Backend

Local FastAPI demo backend for the Sysco Intelligent Supplier Collaboration Portal.

## Run

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Demo Endpoints

```text
GET  /health
POST /pipeline/run-demo/bid_a
POST /pipeline/run-demo/bid_b
POST /pipeline/run-demo/both
POST /pipeline/reset-memory
```

Use `POST /pipeline/run-demo/both` for the main demo path: Bid A runs cold,
then Bid B reuses institutional memory from Bid A in the same request.

## Tests

```powershell
cd backend
python -m pytest tests -p no:cacheprovider
```

The cache provider is disabled because this workspace can block writes to
`.pytest_cache` in some sessions.
