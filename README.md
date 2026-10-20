# Expense Tracker — DevOps Experiment 10

A small Flask + SQLite expense tracking application prepared for an end-to-end DevOps pipeline.

## Features
- Add and delete expenses
- View expense totals and categories
- SQLite persistence
- Health endpoint: `/health`
- Prometheus metrics endpoint: `/metrics`
- Automated tests with PyTest

## Run on Windows

```bat
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m pytest -v
python app.py
```

Open http://127.0.0.1:5000

## Endpoints
- `/` — Expense Tracker page
- `/health` — application/database health check
- `/metrics` — Prometheus-format HTTP request metrics

## DevOps pipeline plan
Git/GitHub → Jenkins → PyTest → Docker build → deployment → Prometheus → Grafana/alerting.
