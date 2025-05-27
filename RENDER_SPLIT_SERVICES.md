# Render.com Multi-Service Setup: Separate Frontend and Backend

## 1. Frontend (Streamlit)
- **Service type:** Web Service
- **Start command:**
  ```
  streamlit run frontend.py --server.port=$PORT --server.address=0.0.0.0
  ```
- **Exposes:** The Streamlit dashboard at your Render web URL.

## 2. Backend (Agent)
- **Service type:** Background Worker (or Web Service if you want HTTP endpoints)
- **Start command:**
  ```
  python agent.py
  ```
- **Exposes:** The backend agent logic (no web interface).

## 3. Example render.yaml

```yaml
services:
  - type: web
    name: moving-frontend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run frontend.py --server.port=$PORT --server.address=0.0.0.0
    envVars:
      - key: DATABASE_URL
        sync: false

  - type: worker
    name: moving-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python agent.py
    envVars:
      - key: DATABASE_URL
        sync: false
```

- Both services share the same codebase and database.
- Set the `DATABASE_URL` environment variable in both services (pointing to the same PostgreSQL instance).

## 4. Summary
- You can now deploy and scale frontend and backend independently on Render.com.
- No code changes are needed for this separation beyond what is already done.
