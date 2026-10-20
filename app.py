import os
import sqlite3
from datetime import date
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, url_for
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

REQUEST_COUNT = Counter(
    "expense_tracker_http_requests_total",
    "Total HTTP requests handled by the Expense Tracker",
    ["method", "endpoint", "status"],
)


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        DATABASE=os.environ.get(
            "DB_PATH", str(Path(app.instance_path) / "expenses.db")
        ),
    )

    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)

    def get_db():
        connection = sqlite3.connect(app.config["DATABASE"])
        connection.row_factory = sqlite3.Row
        return connection

    def init_db():
        with get_db() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    amount REAL NOT NULL CHECK(amount > 0),
                    category TEXT NOT NULL,
                    expense_date TEXT NOT NULL
                )
            """)

    init_db()

    @app.after_request
    def record_request(response):
        REQUEST_COUNT.labels(
            request.method, request.endpoint or "unknown", str(response.status_code)
        ).inc()
        return response

    @app.route("/")
    def index():
        with get_db() as db:
            expenses = db.execute(
                "SELECT * FROM expenses ORDER BY expense_date DESC, id DESC"
            ).fetchall()
            total = db.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM expenses"
            ).fetchone()[0]
        return render_template(
            "index.html", expenses=expenses, total=total,
            today=date.today().isoformat()
        )

    @app.route("/add", methods=["POST"])
    def add_expense():
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "").strip()
        amount_text = request.form.get("amount", "").strip()
        expense_date = request.form.get("expense_date", "").strip()

        try:
            amount = float(amount_text)
            valid_amount = 0 < amount < float("inf")
        except (ValueError, TypeError):
            valid_amount, amount = False, 0

        try:
            date.fromisoformat(expense_date)
            valid_date = True
        except (ValueError, TypeError):
            valid_date = False

        if (not title or len(title) > 100 or not category or len(category) > 50
                or not valid_amount or not valid_date):
            flash("Enter a valid title, category, amount, and date.", "error")
            return redirect(url_for("index"))

        with get_db() as db:
            db.execute(
                """INSERT INTO expenses (title, amount, category, expense_date)
                   VALUES (?, ?, ?, ?)""",
                (title, amount, category, expense_date),
            )
        flash("Expense added successfully!", "success")
        return redirect(url_for("index"))

    @app.route("/delete/<int:expense_id>", methods=["POST"])
    def delete_expense(expense_id):
        with get_db() as db:
            cursor = db.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        if cursor.rowcount:
            flash("Expense deleted successfully.", "success")
        else:
            flash("Expense not found.", "error")
        return redirect(url_for("index"))

    @app.route("/health")
    def health():
        try:
            with get_db() as db:
                db.execute("SELECT 1")
            return {"status": "healthy"}, 200
        except sqlite3.Error:
            return {"status": "unhealthy"}, 500

    @app.route("/metrics")
    def metrics():
        return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
