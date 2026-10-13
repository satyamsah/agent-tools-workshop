"""
Exercise 2 — Add Tools
========================
Give Claude two tools: query_database and search_knowledge_base.
Now it can access real data and real policy documents.

Watch:
  - Which questions trigger a tool call
  - Which questions Claude answers directly (no tool needed)
  - What Claude passes as input to each tool

Your job:
  Step 1 — run the agent with one tool (query_database only)
  Step 2 — add the second tool (search_knowledge_base)
  Step 3 — observe how Claude decides which tool to call

Run:  python exercises/02-add-tools/exercise.py
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

# ── Step 1: One tool — query_database only ────────────────────────────────

console.print(Rule("[bold]Step 1 — One tool: query_database[/bold]"))
console.print("[dim]Claude can query the database but has no policy documents.[/dim]\n")

# TODO: UNCOMMENT STEP 1 AND RE-RUN
# questions_step1 = [
#     "Which vendors have overdue invoices?",
#     "What is our payment policy for overdue invoices?",   # ← no tool for this yet
# ]
#
# for q in questions_step1:
#     console.print(f"[bold cyan]Q:[/bold cyan] {q}")
#     answer = run_agent(q, tools=[QUERY_DATABASE_SCHEMA], verbose=True)
#     console.print(Panel(answer, title="Agent", border_style="green"))
#     console.print()
#
# console.print("[dim]Notice: Q2 (policy question) — Claude either guesses or says it doesn't know.[/dim]")
# console.print("[dim]It has no tool to look up the policy. We fix that in Step 2.[/dim]\n")


# ── Step 2: Two tools — query_database + search_knowledge_base ────────────

console.print(Rule("[bold]Step 2 — Two tools: database + knowledge base[/bold]"))
console.print("[dim]Now Claude can answer BOTH data questions AND policy questions.[/dim]\n")

# TODO: UNCOMMENT STEP 2 AND RE-RUN
# questions_step2 = [
#     "Which vendors have overdue invoices?",               # → query_database
#     "What is our payment policy for overdue invoices?",   # → search_knowledge_base
#     "What is a three-way match?",                         # → search_knowledge_base
#     "How many purchase orders were raised in Q3 2024?",   # → query_database
# ]
#
# for q in questions_step2:
#     console.print(f"[bold cyan]Q:[/bold cyan] {q}")
#     answer = run_agent(q, tools=[QUERY_DATABASE_SCHEMA, SEARCH_KB_SCHEMA], verbose=True)
#     console.print(Panel(answer, title="Agent", border_style="green"))
#     console.print()


# ── Step 3: Watch Claude decide ───────────────────────────────────────────

console.print(Rule("[bold]Step 3 — Watch Claude decide which tool to call[/bold]"))
console.print("[dim]Same two tools. Mixed questions. Observe Claude's decisions.[/dim]\n")

# TODO: UNCOMMENT STEP 3 AND RE-RUN
# mixed_questions = [
#     "What is a purchase order?",                          # → no tool (general knowledge)
#     "What is our total spend with German vendors?",       # → query_database
#     "What are the onboarding requirements for new vendors?", # → search_knowledge_base
#     "How many vendors are rated High risk?",              # → query_database
# ]
#
# for q in mixed_questions:
#     console.print(f"[bold cyan]Q:[/bold cyan] {q}")
#     answer = run_agent(q, tools=[QUERY_DATABASE_SCHEMA, SEARCH_KB_SCHEMA], verbose=True)
#     console.print(Panel(answer, title="Agent", border_style="green"))
#     console.print()
#
# console.print("[dim]Key observation: Claude does NOT call a tool for Q1 — it already knows.[/dim]")
# console.print("[dim]Tool descriptions control when Claude calls each tool.[/dim]")

# ── Pop Quiz ──────────────────────────────────────────────────────────────
#
# "You give Claude two tools but it calls the wrong one. What do you fix?"
# A) Change the model
# B) Rewrite the tool description
# C) Add more tools
#
# Answer: B — the tool description is what Claude reads to decide.
# A better description = better tool selection.

console.print("[dim]Uncomment steps above one at a time and re-run.[/dim]")
