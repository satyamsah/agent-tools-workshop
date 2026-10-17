"""
Exercise 1 — Bare Claude (No Tools)
=====================================
The simplest possible setup — just Claude, no tools.
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

console.print(Rule("[bold]Exercise 1 — Bare Claude (No Tools)[/bold]"))
console.print("[dim]Claude answers from its own knowledge only — no database, no documents.[/dim]\n")

questions = [
    "What is a purchase order?",
    "Which of our vendors have overdue invoices right now?",
    "What is our organisation's payment policy for late invoices?",
]

for i, q in enumerate(questions, 1):
    console.print(f"[bold cyan]Q{i}:[/bold cyan] {q}")
    answer = ask(q)
    console.print(Panel(answer, title="Claude", border_style="green"))
    console.print()

console.print(Panel(
    "Q1 (What is a PO?) → answered correctly — general business knowledge from training\n"
    "Q2 (Which vendors have overdue invoices?) → fails or hallucinates — Claude has no database\n"
    "Q3 (What is our payment policy?) → fails or makes something up — Claude has no policy docs\n\n"
    "Claude is only as good as its training data.\n"
    "It cannot answer YOUR questions about YOUR data.\n\n"
    "Fix: give Claude tools to access real data. → Exercise 2.",
    title="[bold]What you saw[/bold]", border_style="yellow"
))

console.print(Panel(
    "Every response from Claude has two fields you care about:\n\n"
    "  response.stop_reason      = 'end_turn'\n"
    "  response.content[0].type  = 'text'\n"
    "  response.content[0].text  = 'A purchase order is...'\n\n"
    "No tools → stop_reason is always 'end_turn'.\n"
    "In Exercise 2 you will see a second value: 'tool_use'.",
    title="[bold]The response object[/bold]", border_style="cyan"
))

# ── Pop Quiz ──────────────────────────────────────────────────────────────
#
# "Claude answered Q1 correctly without tools. Why?"
# A) It searched the internet
# B) It knows general business concepts from training
# C) It guessed
#
# Answer: B — Claude knows general concepts. It does NOT know YOUR data.
