"""
pipeline/orchestrator.py — routes a goal to the right skill via invoke_skill.

Pattern (same as Joule's agentLoop.ts):
  1. Scan .claude/skills/*/SKILL.md — read name + description from frontmatter
  2. Build skill index: "- name: description" for each skill
  3. Give Claude the index + invoke_skill as the ONLY tool
  4. Claude reads descriptions, picks best skill, calls invoke_skill(skill="...")
  5. Load that SKILL.md body, run the agent loop with real tools + skill instructions
"""

import os
import re

from dotenv import load_dotenv
import anthropic

load_dotenv()

SKILLS_DIR = os.path.join(os.path.dirname(__file__), "../.claude/skills")


def _parse_frontmatter(content: str) -> dict:
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}
    result = {}
    for line in match.group(1).splitlines():
        idx = line.find(":")
        if idx == -1:
            continue
        key, val = line[:idx].strip(), line[idx + 1:].strip()
        if key and val:
            result[key] = val
    return result


def _strip_frontmatter(content: str) -> str:
    return re.sub(r"^---\n.*?\n---\n?", "", content, flags=re.DOTALL).strip()


def load_skill_index() -> list[dict]:
    """Scan .claude/skills/*/SKILL.md — return [{name, description, body}]."""
    skills = []
    for entry in sorted(os.listdir(SKILLS_DIR)):
        path = os.path.join(SKILLS_DIR, entry, "SKILL.md")
        if not os.path.isfile(path):
            continue
        content = open(path).read()
        fm = _parse_frontmatter(content)
        # skip Claude Code workshop skills (bare-agent, one-tool, etc)
        if fm.get("allowed-tools") == "Read":
            continue
        name = fm.get("name", entry)
        description = fm.get("description", name)
        skills.append({"name": name, "description": description, "body": _strip_frontmatter(content)})
    return skills


INVOKE_SKILL_SCHEMA = {
    "name": "invoke_skill",
    "description": "Invoke a skill to handle the request. ALWAYS call this first — pick the single best matching skill.",
    "input_schema": {
        "type": "object",
        "properties": {
            "skill":  {"type": "string", "description": "Name of the skill to invoke"},
            "reason": {"type": "string", "description": "Why this skill matches the request"},
        },
        "required": ["skill", "reason"],
    },
}


def run_orchestrator(goal: str, verbose: bool = True) -> str:
    """
    Route a goal to the right skill and run it.

    Phase 1 — routing:   Claude reads skill index, calls invoke_skill(skill="...")
    Phase 2 — execution: skill instructions become the system prompt, real tools run
    """
    from pipeline.tools import run_tool, QUERY_DATABASE_SCHEMA, SEARCH_KB_SCHEMA

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    skills = load_skill_index()

    # Build the index Claude reads to decide which skill to call
    index = "\n".join(f"- {s['name']}: {s['description']}" for s in skills)

    if verbose:
        print(f"\n  Skill index:\n" + "\n".join(f"    {l}" for l in index.splitlines()) + "\n")

    # ── Phase 1: routing ──────────────────────────────────────────────────
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        system=f"You are a skill router.\n\nAvailable skills:\n{index}\n\nCall invoke_skill immediately. Do not answer the question yourself.",
        tools=[INVOKE_SKILL_SCHEMA],
        messages=[{"role": "user", "content": goal}],
    )

    skill_name = None
    for block in response.content:
        if block.type == "tool_use" and block.name == "invoke_skill":
            skill_name = block.input.get("skill")
            reason = block.input.get("reason", "")

    if not skill_name:
        return "Router did not pick a skill."

    if verbose:
        print(f"  → invoke_skill('{skill_name}')  {reason}")

    skill = next((s for s in skills if s["name"] == skill_name), None)
    if not skill:
        return f"Skill '{skill_name}' not found."

    # ── Phase 2: skill execution ──────────────────────────────────────────
    # Skill body becomes the system prompt — Claude follows its fixed instructions
    messages = [{"role": "user", "content": goal}]

    while True:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            system=skill["body"],
            tools=[QUERY_DATABASE_SCHEMA, SEARCH_KB_SCHEMA],
            messages=messages,
        )

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    if verbose:
                        print(f"  → [{skill_name}] {block.name}({block.input})")
                    result = run_tool(block.name, block.input)
                    if verbose:
                        print(f"  ← {result[:100].replace(chr(10), ' ')}...")
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
