"""
Exercise 4 — Tool Chaining
============================
Think of this as a junior analyst.
You hand it one specific question — it looks up exactly what you asked and stops.

The question itself defines the scope. Claude makes 2 tool calls and is done.
It waits for your next question.

Run:  python exercises/04-tool-chaining/exercise.py
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
from pipeline.tools import QUERY_DATABASE_SCHEMA, SEARCH_KB_SCHEMA

console = Console()

console.print(Rule("[bold]Exercise 4 — Tool Chaining[/bold]"))
console.print("[dim]Questions that need BOTH tools. Count the round trips.[/dim]\n")

questions = [
    "Which vendors have overdue invoices and what does our policy say about how to handle them?",
    "Which high-risk vendors do we have active POs with, and what does policy say about high-risk vendors?",
]

for q in questions:
    console.print(f"[bold cyan]Q:[/bold cyan] {q}\n")
    answer = run_agent(q, tools=[QUERY_DATABASE_SCHEMA, SEARCH_KB_SCHEMA], verbose=True)
    console.print(Panel(answer, title="Claude", border_style="green"))
    console.print()

# ── Pop Quiz ──────────────────────────────────────────────────────────────
#
# "In tool chaining, who decides the ORDER tools are called?"
# A) You hardcode the sequence
# B) Claude decides dynamically based on what it needs next
# C) The tool descriptions define the order
#
# Answer: B — Claude decides after each result whether it needs more
# information or can answer. The order emerges from the question.
