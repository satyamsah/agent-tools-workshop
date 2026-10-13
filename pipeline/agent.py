"""
pipeline/agent.py — the agent loop used throughout the workshop.

This is the COMPLETE working version. Exercises build it step by step.

The agent loop:
  1. Send user message + tool definitions to Claude
  2. If Claude calls a tool → run it → send result back → repeat
  3. If Claude replies with text → return it to the user

Run end-to-end:
  python pipeline/agent.py
"""

import os
import sys
import warnings
import logging

warnings.filterwarnings("ignore")
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("HF_HUB_VERBOSITY", "error")

from dotenv import load_dotenv
import anthropic

load_dotenv()

SYSTEM_PROMPT = """You are a procurement data analyst assistant for an enterprise organisation.
You help analysts answer questions about purchase orders, vendors, invoices, and procurement policies.

You have access to three tools:
  - query_database: for any question involving numbers, data, counts, or amounts
  - search_knowledge_base: for questions about policies, processes, or procedures
  - generate_report: for full reports or analysis that need both data and context

Always use a tool when the question requires data or policy information.
Be concise — summarise tool results clearly, do not dump raw data at the user."""


def run_agent(question: str, tools: list, verbose: bool = True) -> str:
    """
    Run the agent loop for a single question.

    Parameters
    ----------
    question : str
        The user's question.
    tools : list
        List of tool schemas to pass to Claude.
    verbose : bool
        If True, print each tool call as it happens.

    Returns
    -------
    str
        The agent's final answer.
    """
    from pipeline.tools import run_tool

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    messages = [{"role": "user", "content": question}]

    while True:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        )

        # ── Tool call ─────────────────────────────────────────────────────
        if response.stop_reason == "tool_use":
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    if verbose:
                        print(f"  → calling tool: {block.name}({block.input})")

                    result = run_tool(block.name, block.input)

                    if verbose:
                        preview = result[:120].replace("\n", " ")
                        print(f"  ← result: {preview}...")

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            # add Claude's tool call and the results to the conversation
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user",      "content": tool_results})

        # ── Final answer ──────────────────────────────────────────────────
        elif response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text.strip()
            return ""

        else:
            return f"Unexpected stop reason: {response.stop_reason}"


# ── Smoke test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

    from rich.console import Console
    from rich.panel import Panel
    from rich.rule import Rule
    from pipeline.tools import ALL_TOOLS

    console = Console()
    console.print(Rule("[bold]Procurement Agent — live demo[/bold]"))

    questions = [
        "Which vendors have overdue invoices?",
        "What is our policy for late payments?",
        "Give me a vendor performance report for Q3 2024",
    ]

    for q in questions:
        console.print(f"\n[bold cyan]Q:[/bold cyan] {q}")
        answer = run_agent(q, ALL_TOOLS, verbose=True)
        console.print(Panel(answer, title="Agent", border_style="green"))

    console.print(Rule("[bold]Try your own question[/bold]"))
    console.print("[dim]Type any procurement question. Press Enter on blank line to quit.[/dim]\n")
    while True:
        try:
            q = input("Question: ").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if not q:
            break
        answer = run_agent(q, ALL_TOOLS, verbose=True)
        console.print(Panel(answer, title="Agent", border_style="green"))
        console.print()
