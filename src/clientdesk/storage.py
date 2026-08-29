from __future__ import annotations

import json
import secrets
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


class Storage:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def initialize(self, business: dict[str, Any], seed_demo_data: bool = False) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portal_token TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    company TEXT NOT NULL,
                    email TEXT NOT NULL,
                    project_name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    progress INTEGER NOT NULL DEFAULT 0,
                    due_date TEXT NOT NULL DEFAULT '',
                    plan TEXT NOT NULL DEFAULT 'Standard',
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS milestones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                    title TEXT NOT NULL,
                    detail TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'upcoming',
                    due_date TEXT NOT NULL DEFAULT '',
                    sort_order INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS deliverables (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    note TEXT NOT NULL DEFAULT '',
                    kind TEXT NOT NULL DEFAULT 'file',
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS approvals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                    title TEXT NOT NULL,
                    details TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'pending',
                    response TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    responded_at TEXT
                );
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                    reference TEXT NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT NOT NULL DEFAULT 'USD',
                    status TEXT NOT NULL DEFAULT 'pending',
                    due_date TEXT NOT NULL DEFAULT '',
                    payment_url TEXT NOT NULL DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS updates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                    body TEXT NOT NULL,
                    visibility TEXT NOT NULL DEFAULT 'client',
                    created_at TEXT NOT NULL
                );
                """
            )
            connection.execute(
                "INSERT OR IGNORE INTO settings (id, payload, updated_at) VALUES (1, ?, ?)",
                (json.dumps(business), iso()),
            )
        if seed_demo_data:
            self._seed_demo()

    def _seed_demo(self) -> None:
        with self.connect() as connection:
            count = connection.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
            if count:
                return
        maya = self.create_client(
            {
                "name": "Maya Chen",
                "company": "Northlight Advisory",
                "email": "maya@example.com",
                "project_name": "Client onboarding redesign",
                "status": "active",
                "progress": 68,
                "due_date": "2026-09-12",
                "plan": "Standard",
            }
        )
        client_id = maya["id"]
        for order, item in enumerate(
            [
                (
                    "Discovery and content",
                    "Goals, audience, and source material",
                    "complete",
                    "2026-08-24",
                ),
                (
                    "Portal experience",
                    "Dashboard, onboarding, and client journey",
                    "complete",
                    "2026-08-28",
                ),
                (
                    "Review and approvals",
                    "Final copy and visual approval",
                    "in_progress",
                    "2026-09-03",
                ),
                (
                    "Launch and handoff",
                    "Production launch and documentation",
                    "upcoming",
                    "2026-09-12",
                ),
            ]
        ):
            self.create_milestone(
                client_id,
                {
                    "title": item[0],
                    "detail": item[1],
                    "status": item[2],
                    "due_date": item[3],
                    "sort_order": order,
                },
            )
        self.create_deliverable(
            client_id,
            {
                "title": "Project direction brief",
                "url": "https://example.com",
                "note": "Approved project goals and experience principles",
                "kind": "document",
            },
        )
        self.create_deliverable(
            client_id,
            {
                "title": "Interactive portal preview",
                "url": "https://example.com",
                "note": "Responsive prototype for desktop and mobile",
                "kind": "preview",
            },
        )
        self.create_approval(
            client_id,
            {
                "title": "Approve final onboarding copy",
                "details": "Review the welcome message, checklist labels, and completion screen.",
            },
        )
        self.create_invoice(
            client_id,
            {
                "reference": "INV-1042",
                "amount": 1200,
                "currency": "USD",
                "status": "paid",
                "due_date": "2026-08-21",
                "payment_url": "",
            },
        )
        self.create_invoice(
            client_id,
            {
                "reference": "INV-1048",
                "amount": 800,
                "currency": "USD",
                "status": "pending",
                "due_date": "2026-09-05",
                "payment_url": "https://example.com",
            },
        )
        self.create_update(
            client_id,
            {
                "body": (
                    "The portal experience is ready for review. The next decision is the "
                    "final onboarding copy."
                ),
                "visibility": "client",
            },
        )

    def ping(self) -> bool:
        with self.connect() as connection:
            return connection.execute("SELECT 1").fetchone()[0] == 1

    def get_settings(self) -> dict[str, Any]:
        with self.connect() as connection:
            row = connection.execute("SELECT payload FROM settings WHERE id = 1").fetchone()
        return json.loads(row["payload"])

    def update_settings(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self.connect() as connection:
            connection.execute(
                "UPDATE settings SET payload = ?, updated_at = ? WHERE id = 1",
                (json.dumps(payload), iso()),
            )
        return self.get_settings()

    def create_client(self, payload: dict[str, Any]) -> dict[str, Any]:
        token = secrets.token_urlsafe(18)
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO clients (
                    portal_token, name, company, email, project_name, status,
                    progress, due_date, plan, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    token,
                    payload["name"],
                    payload["company"],
                    payload["email"],
                    payload["project_name"],
                    payload.get("status", "active"),
                    payload.get("progress", 0),
                    payload.get("due_date", ""),
                    payload.get("plan", "Standard"),
                    iso(),
                ),
            )
            client_id = cursor.lastrowid
        return self.get_client(client_id)

    def get_client(self, client_id: int) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM clients WHERE id = ?", (client_id,)).fetchone()
        return dict(row) if row else None

    def get_client_by_token(self, token: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM clients WHERE portal_token = ?", (token,)
            ).fetchone()
        return dict(row) if row else None

    def list_clients(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM clients ORDER BY created_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def update_client(self, client_id: int, payload: dict[str, Any]) -> dict[str, Any] | None:
        allowed = {"status", "progress", "due_date", "project_name", "plan"}
        fields = {key: value for key, value in payload.items() if key in allowed}
        if not fields:
            return self.get_client(client_id)
        assignments = ", ".join(f"{key} = ?" for key in fields)
        with self.connect() as connection:
            connection.execute(
                f"UPDATE clients SET {assignments} WHERE id = ?",  # noqa: S608
                (*fields.values(), client_id),
            )
        return self.get_client(client_id)

    def create_milestone(self, client_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO milestones (client_id, title, detail, status, due_date, sort_order)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    client_id,
                    payload["title"],
                    payload.get("detail", ""),
                    payload.get("status", "upcoming"),
                    payload.get("due_date", ""),
                    payload.get("sort_order", 0),
                ),
            )
            row = connection.execute(
                "SELECT * FROM milestones WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        return dict(row)

    def update_milestone(self, milestone_id: int, status: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            connection.execute(
                "UPDATE milestones SET status = ? WHERE id = ?", (status, milestone_id)
            )
            row = connection.execute(
                "SELECT * FROM milestones WHERE id = ?", (milestone_id,)
            ).fetchone()
        return dict(row) if row else None

    def create_deliverable(self, client_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO deliverables (client_id, title, url, note, kind, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    client_id,
                    payload["title"],
                    payload["url"],
                    payload.get("note", ""),
                    payload.get("kind", "file"),
                    iso(),
                ),
            )
            row = connection.execute(
                "SELECT * FROM deliverables WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        return dict(row)

    def create_approval(self, client_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO approvals (client_id, title, details, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (client_id, payload["title"], payload.get("details", ""), iso()),
            )
            row = connection.execute(
                "SELECT * FROM approvals WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        return dict(row)

    def respond_to_approval(
        self, client_id: int, approval_id: int, status: str, response: str
    ) -> dict[str, Any] | None:
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE approvals SET status = ?, response = ?, responded_at = ?
                WHERE id = ? AND client_id = ? AND status = 'pending'
                """,
                (status, response, iso(), approval_id, client_id),
            )
            row = connection.execute(
                "SELECT * FROM approvals WHERE id = ? AND client_id = ?",
                (approval_id, client_id),
            ).fetchone()
        return dict(row) if row else None

    def create_invoice(self, client_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO invoices (
                    client_id, reference, amount, currency, status, due_date, payment_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    client_id,
                    payload["reference"],
                    payload["amount"],
                    payload.get("currency", "USD"),
                    payload.get("status", "pending"),
                    payload.get("due_date", ""),
                    payload.get("payment_url", ""),
                ),
            )
            row = connection.execute(
                "SELECT * FROM invoices WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        return dict(row)

    def create_update(self, client_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO updates (client_id, body, visibility, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (client_id, payload["body"], payload.get("visibility", "client"), iso()),
            )
            row = connection.execute(
                "SELECT * FROM updates WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        return dict(row)

    def portal(self, token: str) -> dict[str, Any] | None:
        client = self.get_client_by_token(token)
        if client is None:
            return None
        client_id = client["id"]
        with self.connect() as connection:
            milestones = connection.execute(
                "SELECT * FROM milestones WHERE client_id = ? ORDER BY sort_order, id",
                (client_id,),
            ).fetchall()
            deliverables = connection.execute(
                "SELECT * FROM deliverables WHERE client_id = ? ORDER BY created_at DESC",
                (client_id,),
            ).fetchall()
            approvals = connection.execute(
                "SELECT * FROM approvals WHERE client_id = ? ORDER BY created_at DESC",
                (client_id,),
            ).fetchall()
            invoices = connection.execute(
                "SELECT * FROM invoices WHERE client_id = ? ORDER BY id DESC", (client_id,)
            ).fetchall()
            updates = connection.execute(
                """
                SELECT * FROM updates
                WHERE client_id = ? AND visibility = 'client'
                ORDER BY created_at DESC LIMIT 20
                """,
                (client_id,),
            ).fetchall()
        return {
            "client": client,
            "milestones": [dict(row) for row in milestones],
            "deliverables": [dict(row) for row in deliverables],
            "approvals": [dict(row) for row in approvals],
            "invoices": [dict(row) for row in invoices],
            "updates": [dict(row) for row in updates],
        }

    def overview(self) -> dict[str, Any]:
        with self.connect() as connection:
            clients = connection.execute(
                """
                SELECT COUNT(*) AS total,
                       SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active,
                       ROUND(AVG(progress), 0) AS average_progress
                FROM clients
                """
            ).fetchone()
            pending = connection.execute(
                "SELECT COUNT(*) FROM approvals WHERE status = 'pending'"
            ).fetchone()[0]
            outstanding = connection.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM invoices WHERE status = 'pending'"
            ).fetchone()[0]
        return {
            "clients": clients["total"] or 0,
            "active": clients["active"] or 0,
            "average_progress": clients["average_progress"] or 0,
            "pending_approvals": pending,
            "outstanding": outstanding,
        }
