# HostelEase AI
Educational hostel management prototype. Fictional records only. Local mode supports CRUD, room capacity validation, fee status, mess menu and feedback, complaints, leave status, notices, analytics, PDF summary, local Ollama chatbot and prompt comparison. No actual payment or approval integration. Local app is single operator, not authenticated; bind to localhost only. Public demo is read-only and uses sample records; never upload a local database. No external AI API key required.

## Windows
`python -m venv .venv`

`.\.venv\Scripts\python.exe -m pip install -r requirements.txt`

`ollama list` (Qwen2.5:3b must be installed and Ollama running for live AI.)

`.\.venv\Scripts\python.exe app.py`

Open http://127.0.0.1:5000. To test demo set `$env:AI_PROVIDER="demo"` before running. Set it to `ollama` to return to local mode.

## Render
Push source to a new GitHub repository, excluding .env and *.db. Create a Python web service, free plan if available, build `pip install -r requirements.txt`, start `gunicorn --bind 0.0.0.0:$PORT app:app`, environment AI_PROVIDER=demo. Free service may sleep; data is not durable. Public demo is not production-ready; no authentication or distributed rate limiting. AI outputs are not authoritative.
