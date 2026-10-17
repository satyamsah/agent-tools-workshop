"""
Exercise 5 — The Agent
========================
Think of this as a senior analyst.
You hand it a goal — it decides what to investigate, which tools to call, when it's done.

Same loop. Same tools. Two things changed:
  1. System prompt says "work autonomously until the goal is complete"
  2. Input is a goal, not a question

The goal leaves all decisions to Claude. You have no idea how many tool calls it will make.

Run:  python exercises/05-agent/exercise.py
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
from pipeline.tools import run_tool, QUERY_DATABASE_SCHEMA, SEARCH_KB_SCHEMA

console = Console()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are an autonomous procurement analyst.

You are given a goal — not a single question.
Figure out what to investigate, which tools to call, and when you are done.
Work autonomously until the goal is complete. Do not ask the user for anything."""

TOOLS = [QUERY_DATABASE_SCHEMA, SEARCH_KB_SCHEMA]


def run_agent(goal: str) -> str:
    messages = [{"role": "user", "content": goal}]
    iteration = 0

    while True:
        iteration += 1
        console.print(f"  [dim]── iteration {iteration} ──[/dim]")

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    console.print(f"  → [cyan]{block.name}[/cyan]({block.input})")
                    result = run_tool(block.name, block.input)
                    console.print(f"  ← {result[:100].replace(chr(10), ' ')}...")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

        elif response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text.strip()
            return ""

        else:
            return f"Unexpected stop reason: {response.stop_reason}"


# ── Run ───────────────────────────────────────────────────────────────────

console.print(Rule("[bold]Exercise 5 — The Agent[/bold]"))

goal = """
Audit the procurement health of this organisation and produce a structured report.
Investigate overdue invoices, high-risk vendors, and relevant policies.
Flag any risks and recommend actions.
"""

console.print(Panel(goal.strip(), title="[bold cyan]Goal[/bold cyan]", border_style="cyan"))
console.print()

report = run_agent(goal)

console.print(Panel(report, title="[bold green]Report[/bold green]", border_style="green"))

# ── Pop Quiz ──────────────────────────────────────────────────────────────
#
# "What is the difference between Ex 4 and Ex 5?"
# A) Different API
# B) Different loop
# C) Same loop — goal instead of question, agent decides the steps
#
# Answer: C
