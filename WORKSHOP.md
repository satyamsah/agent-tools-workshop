# AI Agent Workshop — Session 1: Tools and Skills

## What you will build

A procurement data analyst agent that answers real business questions by deciding — on its own — whether to query a database, search policy documents, or run a multi-step skill.

By the end you will understand:
- How the agent loop works (request → tool call → result → request → answer)
- How Claude decides which tool to call and when
- How to write tool descriptions that guide Claude's decisions
- What a skill is and how it differs from a tool
- The full flow: bare agent → one tool → two tools → chaining → skills

---

## Schedule

| Time | Section |
|---|---|
| 0:00 | Setup + intro |
| 0:15 | Part 1 — How the agent loop works |
| 0:35 | Exercise 1 — Bare agent |
| 0:50 | Part 2 — Tools |
| 1:10 | Exercise 2 — Add tools |
| 1:30 | Break (10 min) |
| 1:40 | Part 3 — Tool chaining |
| 1:55 | Exercise 3 — Tool chaining |
| 2:10 | Part 4 — Skills |
| 2:20 | Exercise 4 — Skills |
| 2:40 | Wrap up |

---

## Setup

### Prerequisites
- Python 3.12 (via pyenv)
- Anthropic API key

### Install

```bash
git clone <repo-url>
cd agent-tools-workshop

pyenv install 3.12.14       # skip if already installed
pyenv local 3.12.14

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

### Seed the database

```bash
python data/seed.py
```

This creates `data/erp.db` — a SQLite procurement database with 10 vendors, 50 purchase orders, 50 invoices, and 45 goods receipts.

### Configure

```bash
cp .env.example .env
# add your ANTHROPIC_API_KEY
```

### Verify

```bash
python check_setup.py
```

---

## The domain — ERP Procurement

We use a simplified enterprise procurement system. This is the domain that runs inside SAP, Oracle, and every large company's ERP system.

**Five tables:**

```
vendors          — supplier master: name, country, payment terms, risk rating
materials        — product catalogue: name, category, price, stock level
purchase_orders  — what was ordered, from whom, at what price
invoices         — what vendors billed us, due dates, payment status
goods_receipt    — confirmation that goods were actually delivered
```

**The business process — Procure to Pay (P2P):**

```
Raise PO → Vendor delivers → Goods Receipt → Vendor sends Invoice → Three-way match → Pay
```

This process is the backbone of every procurement question the agent will answer.

**The knowledge base:**

Six internal policy documents:
- Vendor Payment Policy
- Vendor Risk Management Policy
- Three-Way Match Process
- Procurement Lead Times by Category
- Supplier Onboarding Requirements
- Spend Analysis Guidelines

> **Pop Quiz:** "What is a three-way match?"
> - A) Matching three vendors for the same product
> - B) Matching PO + Goods Receipt + Invoice before paying
> - C) A vendor rating system
>
> Answer: B — before paying any invoice, you verify all three match. This is the standard control that prevents fraud and overpayment.

---

## 0:15 — Part 1: How the Agent Loop Works

### The bare minimum

An agent is just a loop. At its simplest:

```
1. Send message to Claude
2. Claude replies
3. Show reply to user
```

No memory. No tools. Just Claude answering from its training knowledge.

This works for general questions. It completely fails for questions about YOUR data.

### Adding tools

A tool is a function you write. You describe it to Claude in JSON. Claude decides when to call it.

The loop becomes:

```
1. Send message + tool definitions to Claude
2. If Claude calls a tool:
     a. Run the function yourself
     b. Send the result back to Claude
     c. Go to step 2
3. If Claude replies with text → show it to the user
```

That's it. That's the entire agent loop.

### The key insight

**Claude never runs any code.** It only says "call this function with these inputs." You run it. You send the result back. Claude decides what to do next.

```
You                          Claude
 |                               |
 |── "Which vendors are overdue?" |
 |── [tool: query_database]  ──→ |
 |                               | thinks: I need data → call query_database
 |←── call query_database ───────|
 |    (sql: SELECT ...)           |
 |  [run SQL]                    |
 |── result: "V004, V007..."  ──→|
 |                               | thinks: I have the data → answer
 |←── "Delta Logistics and..." ──|
```

### Why this matters for interviews

The question "how would you build an agent?" has one correct answer structure:
1. LLM call with tool definitions
2. Parse `stop_reason == "tool_use"`
3. Run the tool
4. Append result to messages
5. Loop until `stop_reason == "end_turn"`

Everything else (memory, reasoning, skills) is built on top of this loop.

> **Pop Quiz:** "In the agent loop, who runs the tool?"
> - A) Claude runs it internally
> - B) The Anthropic API runs it
> - C) Your code runs it
>
> Answer: C — you write the tool, you run it, you send the result back. Claude only decides when and what to call.

---

## 0:35 — Exercise 1: Bare Agent

**Goal:** see exactly what breaks when the agent has no tools.

```bash
python exercises/01-bare-agent/exercise.py
```

Three questions:
1. "What is a purchase order?" — Claude knows this from training ✓
2. "Which of our vendors have overdue invoices?" — Claude has no data ✗
3. "What is our organisation's payment policy?" — Claude has no documents ✗

The failure is clear: Claude can answer general knowledge questions but cannot answer questions about YOUR organisation's data.

> **Presenter note:** 10 minutes. Ask the room — "what would you need to add to fix question 2? And question 3?"

---

## 0:50 — Part 2: Tools

### What a tool definition looks like

```python
QUERY_DATABASE_SCHEMA = {
    "name": "query_database",
    "description": """Query the ERP procurement database to answer questions about
purchase orders, vendors, invoices, materials, and goods receipts.
Use this for questions involving numbers, counts, amounts, dates, or status.""",
    "input_schema": {
        "type": "object",
        "properties": {
            "sql": {
                "type": "string",
                "description": "A valid SQL SELECT statement"
            }
        },
        "required": ["sql"]
    }
}
```

Three parts:
- **name** — what you call it in your code
- **description** — what Claude reads to decide when to use it
- **input_schema** — what Claude must pass when calling it

### The description is everything

Claude reads the description and matches it to the user's question. A vague description = wrong tool selection.

**Bad description:**
```
"description": "A database tool"
```
Claude might call this for policy questions too — it doesn't know what's in the database.

**Good description:**
```
"description": "Use this for questions involving numbers, counts, amounts,
dates, or status. Do NOT use for policy or procedure questions."
```
Now Claude knows exactly when to call it — and when not to.

### What happens when Claude calls a tool

Claude's response changes from `stop_reason = "end_turn"` to `stop_reason = "tool_use"`:

```python
response.stop_reason = "tool_use"
response.content = [
    {
        "type": "tool_use",
        "id": "tool_abc123",
        "name": "query_database",
        "input": {
            "sql": "SELECT v.name, COUNT(i.invoice_id) as overdue FROM invoices i JOIN ..."
        }
    }
]
```

You run the SQL, get results, and send them back:

```python
messages.append({"role": "assistant", "content": response.content})
messages.append({"role": "user", "content": [{
    "type": "tool_result",
    "tool_use_id": "tool_abc123",
    "content": "Delta Logistics | 3 overdue\nEastern Parts | 2 overdue"
}]})
```

Claude now has the data and produces its final answer.

> **Pop Quiz:** "Claude calls query_database but passes the wrong SQL. What do you fix?"
> - A) Rewrite the input_schema
> - B) Improve the tool description with examples of what questions it handles
> - C) Switch to a better model
>
> Answer: B — the description guides Claude's inputs. Add examples of the kinds of questions it should answer and Claude will generate better SQL.

---

## 1:10 — Exercise 2: Add Tools

**Goal:** give Claude tools and watch it decide when to use them.

```bash
python exercises/02-add-tools/exercise.py
```

Step 1: one tool only (query_database). Policy questions still fail.
Step 2: add search_knowledge_base. Both question types now work.
Step 3: mixed questions — watch Claude pick the right tool each time.

The key moment: Claude answers "What is a purchase order?" **without calling any tool** — it already knows. Tool descriptions told it to only use the tools for specific question types.

> **Presenter note:** 20 minutes. After Step 3, ask: "which question did Claude answer without a tool? Why?"

---

## 1:30 — Break (10 minutes)

---

## 1:40 — Part 3: Tool Chaining

### When one tool is not enough

Some questions need both data AND context:

> "Which vendors have overdue invoices and what does our policy say about handling them?"

This needs:
1. `query_database` — get the overdue vendors
2. `search_knowledge_base` — get the payment policy

Claude calls them in sequence — the result of the first informs the second.

### The loop with two tool calls

```
You                              Claude
 |                                   |
 |── question ──────────────────────→|
 |                                   | → call query_database
 |←── tool_use: query_database ──────|
 |  [run SQL]                        |
 |── tool result: overdue vendors ──→|
 |                                   | → call search_knowledge_base
 |←── tool_use: search_knowledge_base|
 |  [run search]                     |
 |── tool result: policy text ──────→|
 |                                   | → I have enough → answer
 |←── final answer ──────────────────|
```

Three round trips. Claude orchestrates the sequence dynamically — it decides after each result whether it needs more tools or can now answer.

### Claude decides the order

You do not hardcode "call database first, then search." Claude decides based on what it needs next.

If the question was "What does our policy say about the vendors who have overdue invoices?" Claude might call `search_knowledge_base` first to understand the policy, then `query_database` to find the vendors. The order depends on the question.

> **Pop Quiz:** "In tool chaining, who decides the order tools are called?"
> - A) You hardcode the sequence
> - B) Claude decides dynamically based on what it needs
> - C) The tool descriptions define the order
>
> Answer: B — Claude decides after each tool result whether it needs more information or can answer.

---

## 1:55 — Exercise 3: Tool Chaining

**Goal:** ask questions that need both tools — watch the chain unfold.

```bash
python exercises/03-tool-chaining/exercise.py
```

Step 1: one chained question — watch two tool calls happen in sequence.
Step 2: more examples — different chains for different question types.
Step 3: the loop table — map each step to who acts and what happens.

> **Presenter note:** 15 minutes. After Step 1, pause and ask the room to count how many round trips they saw.

---

## 2:10 — Part 4: Skills

### Tools vs Skills

| | Tool | Skill |
|---|---|---|
| What it is | One atomic action | Reusable multi-step capability |
| Built from | External system call | Multiple tool calls |
| Claude decides when? | Every time | Once (at design time) |
| Good for | Simple lookups | Complex repeatable tasks |

### What a skill looks like

```python
def generate_report(topic: str, period: str) -> str:
    # Step 1: get spend data from database
    spend = query_database("SELECT vendor, SUM(amount)...")

    # Step 2: get overdue invoices from database
    overdue = query_database("SELECT vendor, COUNT(*)...")

    # Step 3: get policy context from knowledge base
    policy = search_knowledge_base("vendor payment policy")

    # Step 4: format into a structured report
    return f"## Top Vendors\n{spend}\n\n## Overdue\n{overdue}\n\n## Policy\n{policy}"
```

From Claude's perspective, `generate_report` looks identical to `query_database` — it is just a tool in the schema. The multi-step logic is hidden inside the function.

### When to use a skill

Use a skill when:
- The same sequence of tool calls is needed repeatedly
- The question is complex enough that you want to package the logic once
- You want the agent to invoke a capability cleanly without deciding the chain every time

Use raw tools when:
- The question is simple and one tool is enough
- You need flexibility in how tools are combined

> **Pop Quiz:** "What is the difference between a tool and a skill?"
> - A) Skills use a different API
> - B) A skill is a reusable capability built from multiple tool calls
> - C) Skills are always faster
>
> Answer: B — a skill wraps multiple tool calls. From Claude's perspective it looks identical to a single tool.

---

## 2:20 — Exercise 4: Skills

**Goal:** see how a skill packages complexity — and how Claude decides skill vs raw tool.

```bash
python exercises/04-skills/exercise.py
```

Step 1: call `generate_report` directly — see the three internal tool calls it makes.
Step 2: give the agent all three tools — watch it pick skill vs raw tool per question.
Step 3: comparison table — skill vs manual chaining.

> **Presenter note:** 20 minutes. Key moment: two questions that sound similar but one triggers `generate_report` and one triggers `query_database` directly. Ask the room why.

---

## 2:40 — Wrap Up

### What you built today

```
data/seed.py              — 50 POs, 10 vendors, 50 invoices, 45 goods receipts
pipeline/knowledge_base.py — 6 procurement policy documents
pipeline/tools.py         — query_database, search_knowledge_base, generate_report
pipeline/agent.py         — the agent loop: tool call → run → result → loop

Exercise 1                — bare agent: sees the failure without tools
Exercise 2                — add tools: Claude picks the right one
Exercise 3                — tool chaining: Claude chains tools for complex questions
Exercise 4                — skills: package complexity into reusable capabilities
```

### The agent loop — one diagram to remember

```
┌─────────────────────────────────────────┐
│           AGENT LOOP                    │
│                                         │
│  Send message + tools                   │
│         ↓                               │
│  stop_reason == "tool_use"?             │
│    Yes → run tool → send result → loop  │
│    No  → return answer to user          │
└─────────────────────────────────────────┘
```

### Interview cheatsheet

| Question | Answer |
|---|---|
| "How does tool calling work?" | LLM returns tool_use, you run it, send result, loop until end_turn |
| "Who runs the tool?" | Your code — the LLM only decides what to call |
| "How does Claude pick the right tool?" | Tool descriptions — quality of description = quality of decisions |
| "What is a skill?" | A reusable capability built from multiple tool calls, exposed as a single tool |
| "What is tool chaining?" | Claude calls multiple tools in sequence, each result informing the next |

### Session 2 — What's next

Session 1 built the tools layer. Session 2 adds the remaining pillars:

```
Session 1 ✓   Tools + Skills
Session 2     Memory — agent remembers across turns
              Reasoning — ReAct: plan, act, observe, repeat
              MCP — expose your agent as an MCP server
              Evals — how do you know the agent is working?
```

---
