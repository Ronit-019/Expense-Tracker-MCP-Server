import sqlite3
import os
import aiosqlite
from fastmcp import FastMCP

mcp = FastMCP("Expense Tracker")

DB = os.getenv(
    "DATABASE_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "expenses.db")
)


# ---------------- DATABASE SETUP ----------------

async def init_db():
    async with aiosqlite.connect(DB) as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT
            )
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                month TEXT NOT NULL
            )
        """)

        await conn.commit()


async def get_db():
    return await aiosqlite.connect(DB)


# ---------------- EXPENSE TOOLS ----------------

@mcp.tool()
async def create_expense(
    title: str,
    amount: float,
    category: str,
    date: str,
    description: str = ""
) -> dict:
    """Create a new expense."""
    async with aiosqlite.connect(DB) as conn:
        cursor = await conn.execute(
            """INSERT INTO expenses
               (title, amount, category, date, description)
               VALUES (?, ?, ?, ?, ?)""",
            (title, amount, category, date, description)
        )
        await conn.commit()

        return {
            "id": cursor.lastrowid,
            "message": "Expense created"
        }


@mcp.tool()
async def list_expenses(category: str = None) -> list:
    """List expenses, optionally by category."""
    async with aiosqlite.connect(DB) as conn:

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


@mcp.tool()
async def update_expense(
    expense_id: int,
    title: str = None,
    amount: float = None,
    category: str = None,
    date: str = None,
    description: str = None
) -> dict:
    """Update an existing expense."""

    async with aiosqlite.connect(DB) as conn:

        cursor = await conn.execute(
            "SELECT * FROM expenses WHERE id = ?",
            (expense_id,)
        )

        expense = await cursor.fetchone()

        if not expense:
            return {"error": "Expense not found"}

        await conn.execute("""
            UPDATE expenses
            SET title = ?, amount = ?, category = ?, date = ?, description = ?
            WHERE id = ?
        """, (
            title if title is not None else expense[1],
            amount if amount is not None else expense[2],
            category if category is not None else expense[3],
            date if date is not None else expense[4],
            description if description is not None else expense[5],
            expense_id
        ))

        await conn.commit()

    return {"message": "Expense updated"}


@mcp.tool()
async def delete_expense(expense_id: int) -> dict:
    """Delete an expense."""

    async with aiosqlite.connect(DB) as conn:

        cursor = await conn.execute(
            "DELETE FROM expenses WHERE id = ?",
            (expense_id,)
        )

        await conn.commit()

    if cursor.rowcount == 0:
        return {"error": "Expense not found"}

    return {"message": "Expense deleted"}


# ---------------- BUDGET TOOLS ----------------

@mcp.tool()
async def create_budget(
    category: str,
    amount: float,
    month: str
) -> dict:
    """Create a budget for a category and month."""

    async with aiosqlite.connect(DB) as conn:

        cursor = await conn.execute(
            """INSERT INTO budgets (category, amount, month)
               VALUES (?, ?, ?)""",
            (category, amount, month)
        )

        await conn.commit()

    return {
        "id": cursor.lastrowid,
        "message": "Budget created"
    }


@mcp.tool()
async def list_budgets(month: str = None) -> list:
    """List budgets, optionally for a month."""

    async with aiosqlite.connect(DB) as conn:

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


@mcp.tool()
async def update_budget(
    budget_id: int,
    category: str = None,
    amount: float = None,
    month: str = None
) -> dict:
    """Update an existing budget."""

    async with aiosqlite.connect(DB) as conn:

        cursor = await conn.execute(
            "SELECT * FROM budgets WHERE id = ?",
            (budget_id,)
        )

        budget = await cursor.fetchone()

        if not budget:
            return {"error": "Budget not found"}

        await conn.execute("""
            UPDATE budgets
            SET category = ?, amount = ?, month = ?
            WHERE id = ?
        """, (
            category if category is not None else budget[1],
            amount if amount is not None else budget[2],
            month if month is not None else budget[3],
            budget_id
        ))

        await conn.commit()

    return {"message": "Budget updated"}


@mcp.tool()
async def delete_budget(budget_id: int) -> dict:
    """Delete a budget."""

    async with aiosqlite.connect(DB) as conn:

        cursor = await conn.execute(
            "DELETE FROM budgets WHERE id = ?",
            (budget_id,)
        )

        await conn.commit()

    if cursor.rowcount == 0:
        return {"error": "Budget not found"}

    return {"message": "Budget deleted"}


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