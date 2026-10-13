"""
Exercise 1 — Bare Agent (No Tools)
=====================================
The simplest possible agent — just Claude, no tools.
It can only answer from its own training knowledge.

Watch what happens when you ask it something that requires real data.

Run:  python exercises/01-bare-agent/exercise.py
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

import anthropic

console = Console()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are a procurement data analyst assistant.
You help analysts answer questions about purchase orders, vendors, and invoices.
Be concise — 2-3 sentences."""


def ask(question: str) -> str:
    """Send a single question to Claude. No tools, no memory — just the question."""
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": question}],
    )
    return response.content[0].text.strip()


# ── Run three questions ───────────────────────────────────────────────────

console.print(Rule("[bold]Exercise 1 — Bare Agent (No Tools)[/bold]"))
console.print("[dim]Claude answers from its own knowledge only — no database, no documents.[/dim]\n")

questions = [
    "What is a purchase order?",
    "Which of our vendors have overdue invoices right now?",
    "What is our organisation's payment policy for late invoices?",
]

for q in questions:
    console.print(f"[bold cyan]Q:[/bold cyan] {q}")
    answer = ask(q)
    console.print(Panel(answer, title="Agent", border_style="green"))
    console.print()

# ── What did you observe? ──────────────────────────────────────────────────
#
# Question 1: Claude answers well — "what is a PO" is general knowledge.
# Question 2: Claude cannot answer — it has no access to our database.
# Question 3: Claude makes something up or says it doesn't know — it has
#             no access to our internal policy documents.
#
# This is the stateless, tool-less agent problem.
# The agent is only as good as its training data.
#
# Pop Quiz:
#   "Claude answered Q1 correctly without tools. Why?"
#   A) It searched the internet
#   B) It knows general business concepts from training
#   C) It guessed
#
#   Answer: B — Claude knows general concepts. It does NOT know YOUR data.
#
# In Exercise 2 you will give Claude tools to access real data.
