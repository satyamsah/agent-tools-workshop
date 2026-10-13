"""
Exercise 4 — Skills
=====================
A skill is a reusable multi-step capability built from tools.

Instead of the agent deciding which tools to chain every time,
a skill packages the logic once:

  generate_report(topic, period)
    → calls query_database (spend data)
    → calls query_database (overdue invoices)
    → calls search_knowledge_base (policy context)
    → formats everything into a structured report

From the agent's perspective, generate_report looks like a single tool.
The complexity is hidden inside the skill.

Your job:
  Step 1 — call generate_report directly, see what it produces
  Step 2 — let the agent decide whether to use the skill or raw tools
  Step 3 — compare: skill vs manual chaining for the same question

Run:  python exercises/04-skills/exercise.py
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
from rich.table import Table

load_dotenv()

from pipeline.agent import run_agent
from pipeline.tools import (
    QUERY_DATABASE_SCHEMA,
    SEARCH_KB_SCHEMA,
    GENERATE_REPORT_SCHEMA,
    generate_report,
)

console = Console()


# ── Step 1: Call the skill directly ──────────────────────────────────────

console.print(Rule("[bold]Step 1 — Call generate_report directly[/bold]"))
console.print("[dim]See what the skill produces before giving it to the agent.[/dim]\n")

# TODO: UNCOMMENT STEP 1 AND RE-RUN
# console.print("[dim]Running generate_report('vendor performance', 'Q3 2024')...[/dim]\n")
# report = generate_report(topic="vendor performance", period="Q3 2024")
# console.print(Panel(report, title="[yellow]Skill output: generate_report[/yellow]", border_style="yellow"))
# console.print()
# console.print("[dim]The skill called query_database twice and search_knowledge_base once internally.[/dim]")
# console.print("[dim]The agent sees this as a single tool call.[/dim]\n")


# ── Step 2: Agent chooses skill vs raw tools ──────────────────────────────

console.print(Rule("[bold]Step 2 — Agent picks skill or raw tool[/bold]"))
console.print("[dim]All three tools available. Watch which one Claude picks for each question.[/dim]\n")

# TODO: UNCOMMENT STEP 2 AND RE-RUN
# all_tools = [QUERY_DATABASE_SCHEMA, SEARCH_KB_SCHEMA, GENERATE_REPORT_SCHEMA]
#
# questions = [
#     "How many overdue invoices do we have?",                         # → query_database (simple)
#     "What is the three-way match process?",                          # → search_knowledge_base (simple)
#     "Give me a full vendor performance report for Q3 2024",          # → generate_report (complex)
#     "I need a complete procurement analysis for Q3",                 # → generate_report (complex)
# ]
#
# for q in questions:
#     console.print(f"[bold cyan]Q:[/bold cyan] {q}")
#     answer = run_agent(q, tools=all_tools, verbose=True)
#     console.print(Panel(answer, title="Agent", border_style="green"))
#     console.print()


# ── Step 3: Skill vs manual chaining comparison ───────────────────────────

# TODO: UNCOMMENT STEP 3 AFTER STEP 2
# console.print(Rule("[bold]Step 3 — Skill vs manual chaining[/bold]"))
# table = Table(show_header=True, header_style="bold")
# table.add_column("Approach")
# table.add_column("Tool calls")
# table.add_column("Agent decides?")
# table.add_column("Reusable?")
# table.add_column("Good for")
# table.add_row("Raw tools",  "Agent chains them each time", "Yes — every time", "No",  "Simple, flexible queries")
# table.add_row("Skill",      "Packaged once inside skill",  "Once at design",   "Yes", "Complex, repeatable tasks")
# console.print(table)
# console.print()
# console.print("[dim]Skills are not magic — they are just Python functions that call tools.[/dim]")
# console.print("[dim]The power is in packaging complexity once so the agent invokes it cleanly.[/dim]")
# console.print("[dim]In Session 2 the agent will use skills + memory + reasoning together.[/dim]")

# ── Pop Quiz ──────────────────────────────────────────────────────────────
#
# "What is the difference between a tool and a skill?"
# A) Skills use a different API than tools
# B) A skill is a reusable capability built from multiple tool calls
# C) Skills are faster than tools
#
# Answer: B — a skill wraps multiple tool calls into one reusable unit.
# From Claude's perspective it looks identical to a tool.

console.print("[dim]Uncomment steps above one at a time and re-run.[/dim]")
