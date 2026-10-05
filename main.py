import asyncio
import sqlite3
import os
import aiosqlite
from fastmcp import FastMCP
from enum import Enum
import json
import numpy as np
from sentence_transformers import SentenceTransformer

mcp = FastMCP("Expense Tracker")

embedding_model = None

def get_embedding_model():
    global embedding_model

    if embedding_model is None:
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    return embedding_model

DB = os.getenv(
    "DATABASE_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "expenses.db")
)

class CRUDAction(str, Enum):
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"

def init_db_sync():
    os.makedirs(os.path.dirname(DB) or ".", exist_ok=True)
    with sqlite3.connect(DB) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                embedding TEXT
            );
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                month TEXT NOT NULL
            );
        """)

init_db_sync()  # runs on import, not just under __main__

def add_embedding_column():
    with sqlite3.connect(DB) as conn:
        try:
            conn.execute("ALTER TABLE expenses ADD COLUMN embedding TEXT")
        except sqlite3.OperationalError:
            pass


add_embedding_column()
# ---------------- EXPENSE TOOLS ----------------

@mcp.tool()
async def manage_expenses(
    action: CRUDAction,
    expense_id: int = None,
    title: str = None,
    amount: float = None,
    category: str = None,
    date: str = None,
    description: str = None
) -> dict | list:
    """
    Manage expenses using CREATE, READ, UPDATE, or DELETE actions.
    """

    async with aiosqlite.connect(DB) as conn:

        # CREATE
        if action == CRUDAction.CREATE:

            if not all([title, amount is not None, category, date]):
                return {
                    "error": "title, amount, category and date are required"
                }

            model = get_embedding_model()

            text = f"{title}. {category}. {description}"
            embedding = model.encode(text).tolist()

            cursor = await conn.execute(
                """INSERT INTO expenses
                (title, amount, category, date, description, embedding)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    title,
                    amount,
                    category,
                    date,
                    description,
                    json.dumps(embedding)
                )
            )

            await conn.commit()

            return {
                "id": cursor.lastrowid,
                "message": "Expense created"
            }

        # READ
        elif action == CRUDAction.READ:

            if category:
                cursor = await conn.execute(
                    "SELECT * FROM expenses WHERE category = ?",
                    (category,)
                )
            else:
                cursor = await conn.execute(
                    "SELECT * FROM expenses"
                )

            rows = await cursor.fetchall()

            return [
                {
                    "id": r[0],
                    "title": r[1],
                    "amount": r[2],
                    "category": r[3],
                    "date": r[4],
                    "description": r[5]
                }
                for r in rows
            ]

        # UPDATE
        elif action == CRUDAction.UPDATE:

            if expense_id is None:
                return {"error": "expense_id is required"}

            cursor = await conn.execute(
                "SELECT * FROM expenses WHERE id = ?",
                (expense_id,)
            )

            expense = await cursor.fetchone()

            if not expense:
                return {"error": "Expense not found"}

            await conn.execute(
                """
                UPDATE expenses
                SET title = ?, amount = ?, category = ?, date = ?, description = ?
                WHERE id = ?
                """,
                (
                    title if title is not None else expense[1],
                    amount if amount is not None else expense[2],
                    category if category is not None else expense[3],
                    date if date is not None else expense[4],
                    description if description is not None else expense[5],
                    expense_id
                )
            )

            await conn.commit()

            return {
                "id": expense_id,
                "message": "Expense updated"
            }

        # DELETE
        elif action == CRUDAction.DELETE:

            if expense_id is None:
                return {"error": "expense_id is required"}

            cursor = await conn.execute(
                "DELETE FROM expenses WHERE id = ?",
                (expense_id,)
            )

            await conn.commit()

            if cursor.rowcount == 0:
                return {"error": "Expense not found"}

            return {
                "id": expense_id,
                "message": "Expense deleted"
            }


# ---------------- BUDGET TOOLS ----------------

@mcp.tool()
async def manage_budgets(
    action: CRUDAction,
    budget_id: int = None,
    category: str = None,
    amount: float = None,
    month: str = None
) -> dict | list:
    """
    Manage budgets using CREATE, READ, UPDATE, or DELETE actions.
    """

    async with aiosqlite.connect(DB) as conn:

        # CREATE
        if action == CRUDAction.CREATE:

            if not all([category, amount is not None, month]):
                return {
                    "error": "category, amount and month are required"
                }

            cursor = await conn.execute(
                """
                INSERT INTO budgets (category, amount, month)
                VALUES (?, ?, ?)
                """,
                (category, amount, month)
            )

            await conn.commit()

            return {
                "id": cursor.lastrowid,
                "message": "Budget created"
            }

        # READ
        elif action == CRUDAction.READ:

            if month:
                cursor = await conn.execute(
                    "SELECT * FROM budgets WHERE month = ?",
                    (month,)
                )
            else:
                cursor = await conn.execute(
                    "SELECT * FROM budgets"
                )

            rows = await cursor.fetchall()

            return [
                {
                    "id": r[0],
                    "category": r[1],
                    "amount": r[2],
                    "month": r[3]
                }
                for r in rows
            ]

        # UPDATE
        elif action == CRUDAction.UPDATE:

            if budget_id is None:
                return {"error": "budget_id is required"}

            cursor = await conn.execute(
                "SELECT * FROM budgets WHERE id = ?",
                (budget_id,)
            )

            budget = await cursor.fetchone()

            if not budget:
                return {"error": "Budget not found"}

            await conn.execute(
                """
                UPDATE budgets
                SET category = ?, amount = ?, month = ?
                WHERE id = ?
                """,
                (
                    category if category is not None else budget[1],
                    amount if amount is not None else budget[2],
                    month if month is not None else budget[3],
                    budget_id
                )
            )

            await conn.commit()

            return {
                "id": budget_id,
                "message": "Budget updated"
            }

        # DELETE
        elif action == CRUDAction.DELETE:

            if budget_id is None:
                return {"error": "budget_id is required"}

            cursor = await conn.execute(
                "DELETE FROM budgets WHERE id = ?",
                (budget_id,)
            )

            await conn.commit()

            if cursor.rowcount == 0:
                return {"error": "Budget not found"}

            return {
                "id": budget_id,
                "message": "Budget deleted"
            }


# ---------------- ANALYSIS TOOLS ----------------

@mcp.tool()
async def budget_vs_expense(
    month: str,
    category: str = None
) -> dict:
    """Compare budget with actual expenses for a month."""

    async with aiosqlite.connect(DB) as conn:

        if category:

            cursor = await conn.execute(
                """SELECT COALESCE(SUM(amount), 0)
                   FROM budgets
                   WHERE month = ? AND category = ?""",
                (month, category)
            )
            budget = (await cursor.fetchone())[0]

            cursor = await conn.execute(
                """SELECT COALESCE(SUM(amount), 0)
                   FROM expenses
                   WHERE date LIKE ? AND category = ?""",
                (month + "%", category)
            )
            expense = (await cursor.fetchone())[0]

        else:

            cursor = await conn.execute(
                """SELECT COALESCE(SUM(amount), 0)
                   FROM budgets
                   WHERE month = ?"""
                ,
                (month,)
            )
            budget = (await cursor.fetchone())[0]

            cursor = await conn.execute(
                """SELECT COALESCE(SUM(amount), 0)
                   FROM expenses
                   WHERE date LIKE ?""",
                (month + "%",)
            )
            expense = (await cursor.fetchone())[0]

    return {
        "month": month,
        "budget": budget,
        "expense": expense,
        "remaining": budget - expense,
        "over_budget": expense > budget
    }


@mcp.tool()
async def financial_health_score(month: str) -> dict:
    """Calculate a simple financial health score."""

    async with aiosqlite.connect(DB) as conn:

        cursor = await conn.execute(
            """SELECT COALESCE(SUM(amount), 0)
               FROM budgets
               WHERE month = ?""",
            (month,)
        )
        budget = (await cursor.fetchone())[0]

        cursor = await conn.execute(
            """SELECT COALESCE(SUM(amount), 0)
               FROM expenses
               WHERE date LIKE ?""",
            (month + "%",)
        )
        expense = (await cursor.fetchone())[0]

    if budget == 0:
        return {
            "score": 0,
            "status": "No budget available"
        }

    usage = expense / budget

    if usage <= 0.50:
        score = 100
        status = "Excellent"
    elif usage <= 0.75:
        score = 80
        status = "Good"
    elif usage <= 1.00:
        score = 60
        status = "Fair"
    else:
        score = 30
        status = "Needs attention"

    return {
        "month": month,
        "score": score,
        "status": status,
        "budget": budget,
        "expense": expense
    }

@mcp.tool()
async def search_expenses_by_intent(
    query: str,
    limit: int = 5
) -> list:
    """Find expenses using semantic similarity."""

    model = get_embedding_model()

    query_embedding = model.encode(query)

    async with aiosqlite.connect(DB) as conn:
        cursor = await conn.execute(
            """SELECT id, title, amount, category, date,
                      description, embedding
               FROM expenses
               WHERE embedding IS NOT NULL"""
        )

        rows = await cursor.fetchall()

    results = []

    for row in rows:
        expense_embedding = np.array(json.loads(row[6]))

        similarity = np.dot(query_embedding, expense_embedding) / (
            np.linalg.norm(query_embedding) *
            np.linalg.norm(expense_embedding)
        )

        results.append({
            "id": row[0],
            "title": row[1],
            "amount": row[2],
            "category": row[3],
            "date": row[4],
            "description": row[5],
            "similarity": round(float(similarity), 3)
        })

    results.sort(
        key=lambda x: x["similarity"],
        reverse=True
    )

    return results[:limit]


# ---------------- RESOURCES ----------------

@mcp.resource("expense://summary")
async def expense_summary() -> str:
    """Get a simple financial summary."""

    async with aiosqlite.connect(DB) as conn:

        cursor = await conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM expenses"
        )
        total_expense = (await cursor.fetchone())[0]

        cursor = await conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM budgets"
        )
        total_budget = (await cursor.fetchone())[0]

    remaining = total_budget - total_expense

    return (
        f"Total Budget: {total_budget}\n"
        f"Total Expenses: {total_expense}\n"
        f"Remaining: {remaining}"
    )


@mcp.resource("expense://categories")
async def expense_categories() -> str:
    """Get common expense categories."""

    return (
        "Food, Travel, Bills, Shopping, "
        "Entertainment, Health, Education, Other"
    )


# ---------------- PROMPTS ----------------

@mcp.prompt()
async def financial_review() -> str:
    """Review the user's financial situation."""

    return """
Review my financial situation using the available expense and budget tools.

Summarize:
1. Total spending
2. Budget usage
3. Categories where I spend the most
4. Whether I am overspending
5. One or two simple suggestions

Keep the response short and practical.
"""


@mcp.prompt()
async def budget_advice() -> str:
    """Give simple budget advice."""

    return """
Analyze my budgets and expenses.

Use the available tools to compare my spending against my budgets.
Tell me which categories are doing well, which are overspending,
and give simple practical advice for improving my budget.

Keep the response short and easy to understand.
"""


# ---------------- SERVER ----------------

if __name__ == "__main__":

    transport = os.getenv("MCP_TRANSPORT", "stdio")

    if transport == "streamable-http":
        mcp.run(
            transport="streamable-http",
            host="0.0.0.0",
            port=int(os.getenv("PORT", 8000))
        )
    else:
        mcp.run()