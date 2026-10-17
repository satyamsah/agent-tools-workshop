"""
Exercise 3b — Break the Description
=====================================
Same question. Same tools. Only the descriptions change.

Watch what happens when both tools have identical, vague descriptions.

Run:  python exercises/03-two-tools/exercise_b.py
"""

import os
import sys
import warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

load_dotenv()

from pipeline.agent import run_agent

console = Console()

BAD_QUERY_DATABASE_SCHEMA = {
    "name": "query_database",
    "description": "Use this tool to look up information and answer questions.",
    "input_schema": {
        "type": "object",
        "properties": {"sql": {"type": "string", "description": "A SQL query"}},
        "required": ["sql"]
    }
}

BAD_SEARCH_KB_SCHEMA = {
    "name": "search_knowledge_base",
    "description": "Use this tool to look up information and answer questions.",
    "input_schema": {
        "type": "object",
        "properties": {"query": {"type": "string", "description": "Search query"}},
        "required": ["query"]
    }
}

console.print(Rule("[bold]Exercise 3b — Break the Description[/bold]"))
console.print("[dim]Same question. Same tools. Only the descriptions change.[/dim]\n")

console.print(Panel(
    'query_database:        "Use this tool to look up information and answer questions."\n'
    'search_knowledge_base: "Use this tool to look up information and answer questions."\n\n'
    "[dim]Both identical — Claude has no signal. No schema hint. No status values.[/dim]",
    title="[red]BAD descriptions[/red]", border_style="red"
))
console.print()

q = "Which vendors have overdue invoices?"
console.print(f"[bold cyan]Q:[/bold cyan] {q}\n")
bad_answer = run_agent(q, tools=[BAD_QUERY_DATABASE_SCHEMA, BAD_SEARCH_KB_SCHEMA], verbose=True)
console.print(Panel(bad_answer, title="[red]Answer (bad descriptions)[/red]", border_style="red"))
console.print()

console.print(Panel(
    "Watch what happened in the tool calls above:\n"
    "  • Claude guessed column names → SQL errors → multiple retries\n"
    "  • No status hint → used due_date < TODAY instead of status = 'Overdue'\n"
    "  • Wrong answer: more vendors than the correct 5\n\n"
    "Now look at the good description in tools.py:\n"
    '  "Status values: \'Open\', \'Closed\', \'Cancelled\', \'Paid\', \'Overdue\', \'Pending\'"\n'
    "  → Claude reads this and writes WHERE status = 'Overdue' directly, first try",
    title="[red]What went wrong[/red]", border_style="red"
))

# ── Pop Quiz ──────────────────────────────────────────────────────────────
#
# "Claude called the wrong tool and got a SQL error. What do you fix?"
# A) Change the model
# B) Rewrite the tool description
# C) Add more tools
#
# Answer: B — the description is the only signal Claude has.
# Better description = better routing = correct answer first try.
