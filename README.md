# Expense Tracker MCP Server

A simple Expense Tracker built as an MCP (Model Context Protocol) server using **FastMCP** and **SQLite**.

The server allows an MCP client (such as Claude Desktop) to manage expenses and budgets through tools, read financial information through resources, and use predefined financial-analysis prompts.

---

## Features

### Expense Tools
- Create expense
- List expenses
- Update expense
- Delete expense

### Budget Tools
- Create budget
- List budgets
- Update budget
- Delete budget

### Analysis Tools
- Budget vs Expense
- Financial Health Score

### MCP Resources
- `expense://summary`
- `expense://categories`

### MCP Prompts
- `financial_review`
- `budget_advice`

---

## Tech Stack

- Python
- FastMCP
- SQLite
- MCP
- Claude Desktop

---

## Project Structure

```text
Expense-Tracker/
│
├── main.py
├── requirements.txt
├── README.md
├── .gitignore
└── expenses.db   # Created automatically when the server runs (ignored by Git)
```

---

## How It Works

```text
                 MCP Client
              (Claude Desktop)
                     │
                     │ MCP
                     ↓
              FastMCP Server
                     │
          ┌──────────┼──────────┐
          │          │          │
        Tools     Resources   Prompts
          │          │          │
          └──────────┼──────────┘
                     │
                     ↓
                  SQLite
                     │
                     ↓
               expenses.db
```

---

## Setup

### 1. Clone the repository
```bash
git clone <your-repository-url>
cd Expense-Tracker
```

### 2. Create a virtual environment
```bash
python -m venv .venv
```

### 3. Activate the virtual environment

**Windows:**
```cmd
.venv\Scripts\activate
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

### 5. Run the server
```bash
python main.py
```

*The local server runs using the stdio MCP transport. The SQLite database is created automatically on the first run.*

---

## Claude Desktop

The local server can be connected to Claude Desktop through its MCP configuration (`claude_desktop_config.json`).

```json
{
  "mcpServers": {
    "expense-tracker": {
      "command": "C:\\path\\to\\Expense-Tracker\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\path\\to\\Expense-Tracker\\main.py"
      ]
    }
  }
}
```

After connecting the server, Claude can access the Expense Tracker tools, resources, and prompts.

---

## MCP Reference

### Tools

| Tool | Description |
| :--- | :--- |
| `create_expense` | Create a new expense |
| `list_expenses` | List stored expenses |
| `update_expense` | Update an existing expense |
| `delete_expense` | Delete an expense |
| `create_budget` | Create a budget |
| `list_budgets` | List stored budgets |
| `update_budget` | Update an existing budget |
| `delete_budget` | Delete a budget |
| `budget_vs_expense` | Compare budget against expenses |
| `financial_health_score` | Calculate a simple financial health score |

### Resources

- **`expense://summary`**: Provides a summary of the current financial data, including budget and expense information.
- **`expense://categories`**: Provides the available expense categories.

### Prompts

- **`financial_review`**: Provides instructions for reviewing the user's current financial situation using the available expense and budget information.
- **`budget_advice`**: Provides instructions for analyzing spending and suggesting simple budget improvements.

---

## Example Usage

Once connected to Claude Desktop, you can use natural language such as:

- *"Add an expense of ₹500 for dinner, category Food."*
- *"List my expenses."*
- *"Update expense 3 and change the amount to ₹750."*
- *"Delete expense 3."*
- *"Create a Food budget of ₹5000 for October 2026."*
- *"Show my budgets."*
- *"Compare my Food budget with my Food expenses."*
- *"Give me my financial health score."*

The MCP client decides which tool to call based on the request.

---

## Database

The project uses SQLite to keep the implementation simple. No separate database server is required.

On the first run, the application automatically creates `expenses.db` containing the required tables for expenses and budgets.

For a larger multi-user application, SQLite can easily be replaced with PostgreSQL.

---

## Local and Remote Server

The same codebase supports both local and remote MCP usage.

### Local
The local server uses `stdio`:

```text
Claude Desktop ──► stdio ──► main.py ──► SQLite
```

### Remote
The server is also deployed remotely using Streamable HTTP on Horizon:

```text
MCP Client ──► Streamable HTTP ──► Horizon ──► FastMCP Server ──► SQLite
```

The tools, resources, and prompts remain identical in both modes.

---

## Why SQLite?

SQLite was chosen because this is a small MCP project and does not require a separate database server. It keeps the project easy to:
- Run locally
- Understand
- Test
- Deploy
- Extend

For a larger application with multiple users and concurrent access, PostgreSQL would be a better choice.

---

## Project Goal

The goal of this project is to build a small, practical MCP server and understand how MCP tools, resources, prompts, database operations, and different transports work together.

The project intentionally keeps the implementation simple instead of introducing unnecessary production-level abstractions.

---

## Future Improvements

- PostgreSQL support
- Authentication for the remote server
- More financial analysis tools
- Expense filtering by date range
- Monthly spending summaries
- Recurring expenses and budgets
- Better financial insights

---

## License

[MIT](LICENSE)