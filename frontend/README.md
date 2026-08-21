# Frontend Demo

React dashboard for the local Bid A/B team demo.

## Run

Start the backend first:

```powershell
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Then start the frontend:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL and click `Run Bid A/B Demo`.
