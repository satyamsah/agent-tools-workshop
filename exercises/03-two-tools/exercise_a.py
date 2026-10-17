"""
Exercise 3a — Two Tools
=======================
Add a second tool: search_knowledge_base.
Now Claude can answer BOTH data questions AND policy questions.

Watch which tool Claude picks for each question — and why.

Run:  python exercises/03-two-tools/exercise_a.py
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

console.print(Rule("[bold]Exercise 3a — Two Tools[/bold]"))
console.print("[dim]Same agent. Now it has two tools. Watch which one it calls for each question.[/dim]\n")

questions = [
    ("Which vendors have overdue invoices?",             "→ query_database"),
    ("What is our payment policy for overdue invoices?", "→ search_knowledge_base"),
    ("What is our total spend with German vendors?",     "→ query_database"),
    ("What is a purchase order?",                        "→ no tool (Claude already knows)"),
]

for i, (q, hint) in enumerate(questions, 1):
    console.print(f"[bold cyan]Q{i}:[/bold cyan] {q}  [dim]{hint}[/dim]")
    answer = run_agent(q, tools=[QUERY_DATABASE_SCHEMA, SEARCH_KB_SCHEMA], verbose=True)
    console.print(Panel(answer, title="Claude", border_style="green"))
    console.print()

console.print(Panel(
    "Claude routed each question to the right tool — or answered directly without any tool.\n\n"
    "How? It read the description:\n"
    '  query_database:        "Use for numbers, counts, amounts, dates, status"\n'
    '  search_knowledge_base: "Use for policies, procedures, SLAs, guidelines"\n\n'
    "The description IS the routing logic.",
    title="[bold]What you saw[/bold]", border_style="yellow"
))

# ── Pop Quiz ──────────────────────────────────────────────────────────────
#
# "You have two tools. How does Claude know which one to call?"
# A) It tries both and picks the better answer
# B) It reads the description of each tool and picks the best match
# C) It always calls the first tool in the list
#
# Answer: B — the description is the only signal Claude has.
