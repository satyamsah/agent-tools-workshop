"""
Exercise 2 — One Tool: query_database
=======================================
Add one tool to the bare setup.
Now Claude can query the real ERP database.

This exercise shows the full tool-calling loop:

  1. You send a question + tool definition
  2. Claude replies with stop_reason = "tool_use"
  3. You run the tool, get the result
  4. You send the result back
  5. Claude replies with stop_reason = "end_turn" — final answer

Watch the → and ← lines to see each step happen live.

Run:  python exercises/02-one-tool/exercise.py
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
from pipeline.tools import QUERY_DATABASE_SCHEMA

console = Console()

console.print(Rule("[bold]Exercise 2 — One Tool: query_database[/bold]"))
console.print("[dim]Claude can now query the real database. Watch the loop.[/dim]\n")

questions = [
    "Which vendors have overdue invoices?",              # → tool_use → end_turn
    "How many purchase orders were raised in Q3 2024?",  # → tool_use → end_turn
    "What is our payment policy for overdue invoices?",  # → end_turn (no tool for this yet)
]

for i, q in enumerate(questions, 1):
    console.print(f"[bold cyan]Q{i}:[/bold cyan] {q}")
    answer = run_agent(q, tools=[QUERY_DATABASE_SCHEMA], verbose=True)
    console.print(Panel(answer, title="Claude", border_style="green"))
    console.print()

console.print(Panel(
    "Q1 → 1 tool call → stop_reason: tool_use → run SQL → stop_reason: end_turn → answer\n"
    "Q2 → 1 tool call → stop_reason: tool_use → run SQL → stop_reason: end_turn → answer\n"
    "Q3 → 0 tool calls → stop_reason: end_turn immediately → Claude admits it doesn't know\n\n"
    "The loop:\n"
    "  stop_reason = 'tool_use'  → you run the tool, send result back, loop again\n"
    "  stop_reason = 'end_turn'  → Claude has an answer, stop\n\n"
    "Q3 failed because there is no tool for policy docs.\n"
    "Fix: add search_knowledge_base — Exercise 3.",
    title="[bold]What you saw[/bold]", border_style="yellow"
))

console.print(Panel(
    "Iteration 1 — Claude needs a tool:\n"
    "  response.stop_reason      = 'tool_use'\n"
    "  response.content[0].type  = 'tool_use'\n"
    "  response.content[0].name  = 'query_database'\n"
    "  response.content[0].input = {'sql': \"SELECT ... WHERE status = 'Overdue'\"}\n"
    "\n"
    "Iteration 2 — Claude has the result, returns answer:\n"
    "  response.stop_reason      = 'end_turn'\n"
    "  response.content[0].type  = 'text'\n"
    "  response.content[0].text  = '5 vendors have overdue invoices...'\n"
    "\n"
    "Your while loop checks stop_reason after every API call.\n"
    "That single field drives the entire agent loop.",
    title="[bold]The response object[/bold]", border_style="cyan"
))

# ── Pop Quiz ──────────────────────────────────────────────────────────────
#
# "Who runs the tool?"
# A) Claude runs it internally
# B) The Anthropic API runs it
# C) Your code runs it
#
# Answer: C — you write the tool, you run it, you send the result back.
# Claude only decides WHEN to call it and WHAT to pass.
