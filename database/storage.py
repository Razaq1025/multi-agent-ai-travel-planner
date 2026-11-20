import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List


DB_PATH = os.getenv("LOCAL_SQLITE_PATH", os.path.join("database", "travel_plans.db"))


def _get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS trip_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            starting_location TEXT NOT NULL,
            destination TEXT NOT NULL,
            days INTEGER NOT NULL,
            travellers INTEGER NOT NULL,
            total_budget REAL NOT NULL,
            estimated_cost REAL NOT NULL,
            plan_json TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def save_trip_plan(plan_result: Dict[str, Any]) -> int:
    """
    Serializes and saves a completed multi-agent travel plan into local persistent storage.
    """
    req = plan_result["request"]
    expense = plan_result["expense_summary"]

    serializable_payload = {
        "request": req.model_dump(),
        "resolved_destination": plan_result["resolved_destination"],
        "budget_allocation": plan_result["budget_allocation"].model_dump(),
        "destination_output": plan_result["destination_output"].model_dump(),
        "weather_output": plan_result["weather_output"].model_dump(),
        "transport_output": plan_result["transport_output"].model_dump(),
        "accommodation_output": plan_result["accommodation_output"].model_dump(),
        "itinerary_output": plan_result["itinerary_output"].model_dump(),
        "route_metrics": plan_result.get("route_metrics"),
        "review_report": plan_result["review_report"].model_dump(),
        "expense_summary": expense,
        "execution_trace": plan_result["execution_trace"],
    }

    conn = _get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO trip_history (
                created_at, starting_location, destination, days, travellers,
                total_budget, estimated_cost, plan_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                req.starting_location,
                plan_result["resolved_destination"],
                req.days,
                req.travellers,
                req.total_budget,
                float(expense["total_estimated_cost"]),
                json.dumps(serializable_payload),
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        conn.close()


def list_recent_trips(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Returns summary rows of recent saved travel plans.
    """
    conn = _get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, created_at, starting_location, destination, days, travellers,
                   total_budget, estimated_cost
            FROM trip_history
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()