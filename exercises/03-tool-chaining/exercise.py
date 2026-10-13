"""
Exercise 3 — Tool Chaining
============================
Some questions need MORE than one tool.

"Why do we have overdue invoices with German vendors AND what does our policy say?"
→ query_database  (get the overdue invoices)
→ search_knowledge_base  (get the policy)
→ Claude synthesises both into one answer

This is tool chaining — Claude calls multiple tools in sequence,
using the result of one to inform the next.

Watch the req → tool → result → tool → result → answer loop in action.

Run:  python exercises/03-tool-chaining/exercise.py
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
from pipeline.tools import QUERY_DATABASE_SCHEMA, SEARCH_KB_SCHEMA

console = Console()

console.print(Rule("[bold]Exercise 3 — Tool Chaining[/bold]"))
console.print("[dim]Questions that need BOTH tools — watch the chain unfold.[/dim]\n")


# ── Step 1: A question that needs both tools ──────────────────────────────

console.print(Rule("[bold]Step 1 — Chain: database → knowledge base[/bold]"))

# TODO: UNCOMMENT STEP 1 AND RE-RUN
# chained_question = (
#     "Which vendors have overdue invoices and what does our policy say "
#     "about how to handle them?"
# )
# console.print(f"[bold cyan]Q:[/bold cyan] {chained_question}\n")
# answer = run_agent(
#     chained_question,
#     tools=[QUERY_DATABASE_SCHEMA, SEARCH_KB_SCHEMA],
#     verbose=True,
# )
# console.print(Panel(answer, title="Agent", border_style="green"))
# console.print()
# console.print("[dim]You saw two tool calls: first query_database, then search_knowledge_base.[/dim]")
# console.print("[dim]Claude used the DB result to frame the policy search.[/dim]\n")


# ── Step 2: More chaining examples ───────────────────────────────────────

console.print(Rule("[bold]Step 2 — More chaining examples[/bold]"))

# TODO: UNCOMMENT STEP 2 AND RE-RUN
# chained_questions = [
#     "Which high-risk vendors do we have active POs with, and what does policy say about high-risk vendors?",
#     "What materials have low stock and what are the standard lead times for those categories?",
# ]
#
# for q in chained_questions:
#     console.print(f"[bold cyan]Q:[/bold cyan] {q}\n")
#     answer = run_agent(q, tools=[QUERY_DATABASE_SCHEMA, SEARCH_KB_SCHEMA], verbose=True)
#     console.print(Panel(answer, title="Agent", border_style="green"))
#     console.print()


# ── Step 3: The loop visualised ───────────────────────────────────────────

# TODO: UNCOMMENT STEP 3 AFTER RUNNING STEPS 1 AND 2
# console.print(Rule("[bold]Step 3 — The agent loop[/bold]"))
# table = Table(show_header=True, header_style="bold")
# table.add_column("Step")
# table.add_column("Who acts")
# table.add_column("What happens")
# table.add_row("1", "You",    "Send question + tool definitions to Claude")
# table.add_row("2", "Claude", "Decides to call query_database, returns tool_use")
# table.add_row("3", "You",    "Run query_database, get results")
# table.add_row("4", "You",    "Send tool result back to Claude")
# table.add_row("5", "Claude", "Decides to call search_knowledge_base")
# table.add_row("6", "You",    "Run search_knowledge_base, get results")
# table.add_row("7", "You",    "Send tool result back to Claude")
# table.add_row("8", "Claude", "Has enough context, returns final answer (end_turn)")
# console.print(table)
# console.print()
# console.print("[dim]Claude never runs any code. It only decides WHAT to call and WHAT to pass.[/dim]")
# console.print("[dim]You run the tools. You send results back. Claude synthesises.[/dim]")

# ── Pop Quiz ──────────────────────────────────────────────────────────────
#
# "In tool chaining, who decides the ORDER in which tools are called?"
# A) You, by hardcoding the sequence
# B) Claude, based on what it needs next
# C) The tool descriptions define the order
#
# Answer: B — Claude decides dynamically. It calls whatever tool it needs
# next based on what it has already learned from previous tool results.

console.print("[dim]Uncomment steps above one at a time and re-run.[/dim]")
