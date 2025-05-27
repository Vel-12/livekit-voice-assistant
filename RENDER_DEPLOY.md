# Render.com PostgreSQL migration and frontend deployment instructions

## 1. PostgreSQL Setup
- Your code now uses the `DATABASE_URL` environment variable for PostgreSQL.
- In Render.com, add a PostgreSQL database and copy its connection string to your service's environment variables as `DATABASE_URL`.

## 2. Requirements
- `psycopg2-binary` is added to `requirements.txt` for PostgreSQL support.

## 3. Frontend (Streamlit)
- On Render, set your web service start command to:
  
  ```
  streamlit run frontend.py --server.port=10000 --server.address=0.0.0.0
  ```
  (Render will set the port via `$PORT` env var, so you may want to use `--server.port=$PORT`)

- The Streamlit app will be accessible via the Render-provided URL.

## 4. Backend (Agent)
- If you want the backend agent running, deploy it as a separate service with a start command like:
  
  ```
  python agent.py
  ```

## 5. render.yaml
- You may need to split your services in `render.yaml` if you want both frontend and backend running.
- Example for Streamlit frontend:

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
```

- Example for backend agent:

```yaml
  - type: worker
    name: moving-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python agent.py
    envVars:
      - key: DATABASE_URL
        sync: false
```

## 6. Database Migration
- The code will auto-create the table if it doesn't exist. No manual migration needed.

---

**Summary:**
- Set `DATABASE_URL` in your environment variables on Render.
- Use the correct start command for Streamlit.
- Deploy backend as a separate worker if needed.
- No manual DB migration is required; the code will handle it.
