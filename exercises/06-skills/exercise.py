"""
Exercise 6 — Skills
=====================
Same goal as Exercise 5.
But now the steps are packaged in a SKILL.md file.

The orchestrator:
  1. Reads .claude/skills/*/SKILL.md descriptions
  2. Claude calls invoke_skill("procurement-audit") — routes by description
  3. Skill body becomes the system prompt — fixed steps run every time

Open .claude/skills/procurement-audit/SKILL.md to see the fixed steps.

Run:  python exercises/06-skills/exercise.py
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

from pipeline.orchestrator import run_orchestrator

console = Console()

# ── Run ───────────────────────────────────────────────────────────────────

console.print(Rule("[bold]Exercise 6 — Skills[/bold]"))

goal = "Audit the procurement health of this organisation and flag any risks."

console.print(Panel(goal, title="[bold cyan]Goal[/bold cyan]", border_style="cyan"))
console.print()

report = run_orchestrator(goal, verbose=True)

console.print(Panel(report, title="[bold green]Skill Report[/bold green]", border_style="green"))

# ── Pop Quiz ──────────────────────────────────────────────────────────────
#
# "You have 10 skills. How does Claude know which one to call?"
# A) You hardcode the routing
# B) Claude reads the description on each SKILL.md and picks the best match
# C) It tries all 10
#
# Answer: B — same as tool descriptions in Exercise 3, one level up.
