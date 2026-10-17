# AI Agent Workshop — Session 1: Tools and Agents

## What you will build

A procurement analyst that starts as a bare Claude call and ends as a real autonomous agent — one you give a goal to, and it figures out the rest.

By the end you will understand:
- The difference between a tool-calling loop and a real agent
- How Claude decides which tool to call and when
- How to write tool descriptions that guide Claude's decisions
- How tool chaining works — Claude calling multiple tools in sequence
- What makes something an agent: goal-directed, autonomous, decides its own steps

---

## Schedule

| Time | Section |
|---|---|
| 0:00 | Setup + intro |
| 0:15 | Part 1 — How the agent loop works |
| 0:35 | Exercise 1 — Bare agent |
| 0:50 | Part 2 — One tool |
| 1:10 | Exercise 2 — One tool |
| 1:30 | Break (10 min) |
| 1:40 | Part 3 — Two tools + description quality |
| 2:00 | Exercise 3 — Two tools |
| 2:15 | Part 4 — Tool chaining |
| 2:25 | Exercise 4 — Tool chaining |
| 2:40 | Part 5 — What is an agent? |
| 2:50 | Exercise 5 — The Agent |
| 3:00 | Part 6 — Skills |
| 3:10 | Exercise 6 — Skills |
| 3:20 | Best practices + wrap up |

---

## Setup

**Prerequisites:** Python 3.10–3.13, Anthropic API key

**Steps:**

1. Clone the repo
   ```bash
   git clone <repo-url>
   cd agent-tools-workshop
   ```

2. Set Python version (skip if already on 3.10–3.13)
   ```bash
   pyenv install 3.12.14
   pyenv local 3.12.14
   ```

3. Create and activate a virtual environment
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Install dependencies
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. Seed the database
   ```bash
   python data/seed.py
   ```
   This creates `data/erp.db` — 10 vendors, 50 purchase orders, 50 invoices, 45 goods receipts.

6. Add your API key
   ```bash
   cp .env.example .env
   # open .env and add your ANTHROPIC_API_KEY
   ```

7. Verify everything works
   ```bash
   python check_setup.py
   ```

---

## The domain — ERP Procurement

We use a simplified enterprise procurement system. This is the domain that runs inside every large company's ERP system.

**Five tables** — live in `data/erp.db` (SQLite):

```
vendors          — supplier master: name, country, payment terms, risk rating
materials        — product catalogue: name, category, price, stock level
purchase_orders  — what was ordered, from whom, at what price
invoices         — what vendors billed us, due dates, payment status
goods_receipt    — confirmation that goods were actually delivered
```

> Peek at the real data before the exercises — run this once:
>
> ```bash
> python -c "
> import sqlite3
> conn = sqlite3.connect('data/erp.db')
> for table in ['vendors', 'purchase_orders', 'invoices', 'materials', 'goods_receipt']:
>     print(f'\n--- {table} ---')
>     rows = conn.execute(f'SELECT * FROM {table} LIMIT 10').fetchall()
>     cols = [d[0] for d in conn.execute(f'SELECT * FROM {table} LIMIT 0').description]
>     print(' | '.join(cols))
>     for r in rows: print(' | '.join(str(v) for v in r))
> "
> ```

**The business process — Procure to Pay (P2P):**

```
Raise PO (Purchase Order)    — company creates an order: "buy 100 units from Vendor X"
       ↓
Vendor delivers              — goods arrive at the warehouse
       ↓
Goods Receipt                — warehouse confirms delivery matches the PO
       ↓
Vendor sends Invoice         — vendor bills the company
       ↓
Three-way match              — PO + Goods Receipt + Invoice must all match
       ↓
Pay                          — payment goes out to the vendor
```

This process is the backbone of every procurement question the agent will answer.

**The knowledge base** — live in `pipeline/knowledge_base.py`:

Six internal policy documents:
- Vendor Payment Policy
- Vendor Risk Management Policy
- Three-Way Match Process
- Procurement Lead Times by Category
- Supplier Onboarding Requirements
- Spend Analysis Guidelines

> Open `pipeline/knowledge_base.py` to read the full policy text.

> **Pop Quiz:** "What is a three-way match?"
> - A) Matching three vendors for the same product
> - B) Matching PO + Goods Receipt + Invoice before paying
> - C) A vendor rating system
>
> Answer: B — before paying any invoice, you verify all three match. This is the standard control that prevents fraud and overpayment.

---

## 0:15 — Part 1: What is an Agent?

> **Key points to land:**
> - An LLM is a text predictor — tokens in, tokens out. No memory, no actions, no access to your data.
> - An **agent harness** is the scaffolding you write — the loop, tool dispatcher, message history. The infrastructure.
> - An **agent** is the harness + the LLM inside it, behaving goal-directed and autonomously. The harness without the LLM is just plumbing.
> - Tools are what make it useful in your business — without them Claude can only answer from training data, which may be stale or wrong for your specific context.

### The hierarchy

Each layer builds on the one below. Understand the layer before moving up.

```
LLM
  — predicts the next token. Text in, text out. That's it.
  — no memory, no actions, no awareness of your data.
  ↓
Tool
  — a Python function + a JSON schema.
  — gives the LLM a way to act: query a database, search a document, call an API.
  ↓
Harness
  — the loop YOU write: send message → check stop_reason → run tool → send result back.
  — just plumbing. Does nothing intelligent on its own.
  ↓
Agent
  — LLM + tools + harness + a goal.
  — now it can decide what to do, act on the world, and keep going until it's done.
```

This is exactly what you will build today — one layer at a time.

### What is an LLM?

A Large Language Model (LLM) is a neural network trained on massive amounts of text.

It does one thing: **predict the next token**.

```
Input:  "Which vendors have overdue"
Output: "invoices?"

Input:  "The capital of France is"
Output: "Paris"
```

That's it. No memory. No actions. No awareness of your data. Just pattern matching on text it was trained on.

Claude is an LLM. When you call `client.messages.create(...)` you are asking it to predict the next tokens given your input. Nothing more.

### What is an Agent?

An agent is a **system** built around an LLM. The LLM is the brain — but the system gives it:

```
LLM alone:                    Agent system:

Text in → Text out            Goal
                                ↓
                              LLM decides what to do
                                ↓
                              Tool executes the action
                                ↓
                              Result goes back to LLM
                                ↓
                              LLM decides what to do next
                                ↓
                              ... loop until done
```

Three things make a system an agent:

```
1. Tools      — functions the LLM can call to act on the world
2. A loop     — keeps running until the job is done, not just one response
3. Decisions  — LLM decides what to do after each result
```

The LLM never runs code. It only decides **what** to call and **what** to pass. Your code runs the tool. Your loop sends the result back. The LLM decides what to do next.

### What we are building today

```
Exercise 1 — Claude with no tools     → just a text generator, fails on real data
Exercise 2 — Claude + one tool        → can query the database, the loop starts
Exercise 3 — Claude + two tools       → routes by description, covers both data + policy
Exercise 4 — Claude + tool chaining   → calls tools in sequence, decides the order
Exercise 5 — Claude + goal            → fully autonomous, decides all steps itself
Exercise 6 — Claude + skills          → routes to packaged workflows via invoke_skill
```

By Exercise 5 it is a real agent. Exercises 1-4 build the foundation.

### The loop — one diagram

```
┌─────────────────────────────────────────────────────┐
│                  AGENT LOOP                          │
│                                                      │
│  You send: goal + tools                              │
│          ↓                                           │
│  Claude responds                                     │
│          ↓                                           │
│  stop_reason == "tool_use"?                          │
│    Yes → your code runs the tool → send result back  │
│        → loop again                                  │
│    No  → stop_reason == "end_turn"                   │
│        → return answer                               │
└─────────────────────────────────────────────────────┘
```

Two values. That's all your loop checks.

---

### The bare minimum

One request, one response. No loop, no tools — Claude answers from training knowledge only.

```
REQUEST 1:
  messages = [
    {"role": "user", "content": "Which vendors have overdue invoices?"}
  ]

RESPONSE 1:
  stop_reason = "end_turn"    ← always end_turn, no loop
  content     = "In procurement, overdue invoices typically occur
                 when payment terms are exceeded..."
                 ← generic answer, knows nothing about YOUR data
```

**What about remembering earlier messages?**

The messages list IS the memory. Without it, Claude forgets every turn:

```
WITHOUT history (forgets):

  REQUEST 1:
    messages = [{"role": "user", "content": "My name is Alex"}]
  RESPONSE 1: "Hi Alex!"

  REQUEST 2:
    messages = [{"role": "user", "content": "What is my name?"}]
                ← Alex not here
  RESPONSE 2: "I don't know your name."


WITH history (remembers):

  REQUEST 1:
    messages = [{"role": "user", "content": "My name is Alex"}]
  RESPONSE 1: "Hi Alex!"

  REQUEST 2:
    messages = [
      {"role": "user",      "content": "My name is Alex"},  ← kept
      {"role": "assistant", "content": "Hi Alex!"},          ← kept
      {"role": "user",      "content": "What is my name?"}  ← new
    ]
  RESPONSE 2: "Your name is Alex."
```

> The messages list is the memory — you control what stays in it.
> We cover memory management in depth in Session 2.

No memory. No tools. Just Claude answering from its training knowledge.
This works for general questions. It completely fails for questions about YOUR data.

### stop_reason — the only condition you check

Every Claude response has a `stop_reason`. It tells you why Claude stopped:

| stop_reason | Meaning | What you do |
|---|---|---|
| `end_turn` | Claude finished — it has an answer | Show the answer to the user, stop |
| `tool_use` | Claude is not done — it needs to call a tool | Run the tool, send result back, loop again |

```
if stop_reason == "end_turn":
    → show answer, stop

if stop_reason == "tool_use":
    → run the tool, send result back, loop again
```

In the bare agent — no tools — Claude always returns `end_turn` immediately.
There are no tools to call so it just answers and stops. No loop needed.

The agent loop only exists because of `tool_use`.

### Adding tools

A tool is a function you write. You describe it to Claude in JSON. Claude decides when to call it.

The loop becomes:

```
START
  messages = []
  tools = [query_database, search_knowledge_base, generate_report]

  user_input = "Which vendors have overdue invoices?"
  messages = [user_input]

  ── ITERATION 1 ──────────────────────────────────────────────
  response = claude.chat(messages, tools)
  # stop_reason = "tool_use"                ← Claude wants data
  # tool_name   = "query_database"
  # tool_inputs = {"sql": "SELECT v.name FROM vendors v
  #                        JOIN invoices i ON ...
  #                        WHERE i.status = 'Overdue'"}

  result = run("query_database", sql)
  # result = "Delta Logistics GmbH
  #           Eastern Parts Corp"

  messages.append(claude's tool call)       ← add Claude's request
  messages.append(tool result)              ← add your result

  ── ITERATION 2 ──────────────────────────────────────────────
  response = claude.chat(messages, tools)
  # stop_reason = "end_turn"                ← Claude has enough
  # content     = "Two vendors have overdue invoices:
  #                Delta Logistics GmbH and Eastern Parts Corp."

  print answer
STOP
END
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

> **Key points to land:**
> - Q1 works — Claude knows general concepts from training
> - Q2 and Q3 fail — Claude has no access to your database or your documents
> - This failure is the entire motivation for everything that follows

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

> **Key points to land:**
> - A tool is a JSON schema with three parts: name, description, input_schema
> - The description is what Claude reads to decide WHEN to call it and WHAT to pass
> - When Claude calls a tool, `stop_reason` flips to `"tool_use"` — your loop runs the tool and sends the result back

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

## 1:10 — Exercise 2: Add Tools

> **Key points to land:**
> - One tool added — data questions now work
> - Watch the `→` and `←` lines: that is your loop running in real time
> - Q3 still fails — there is no tool for policy docs yet, so Claude admits it doesn't know

**Goal:** give Claude tools and watch it decide when to use them.

```bash
python exercises/02-one-tool/exercise.py
```

Step 1: one tool only (query_database). Data questions work, policy questions fail.
The failure on Q3 is intentional — sets up Exercise 3.

> **Presenter note:** 20 minutes. After running, ask: "which question failed? What would fix it?"

### What happens when Claude calls a tool

Run it first, then read this. Each `→` and `←` line you saw in the terminal maps to one step here.

```
Step 1 — You send the question + tool schema to Claude
  You:    "Which vendors have overdue invoices?"
  You:    [here is a tool called query_database,
           it takes SQL,
           tables are: vendors, invoices, purchase_orders...]

Step 2 — Claude reads everything and decides
  Claude: "This question needs data.
           I have a query_database tool.
           The schema says there's an invoices table with a status column.
           I'll write SQL to answer this."

Step 3 — Claude returns the SQL (does NOT run it)
  Claude → You:  stop_reason = "tool_use"
                 name = "query_database"
                 input = { sql: "SELECT v.name FROM vendors v
                                 JOIN invoices i ...
                                 WHERE i.status = 'Overdue'" }

  ← Claude stops here. It is waiting.

Step 4 — YOUR Python code runs the SQL
  Python:  sqlite3.connect(erp.db)
           cursor.execute(that SQL)
           rows = cursor.fetchall()
           → "Delta Logistics | 3, Eastern Parts | 2"

Step 5 — You send the result back to Claude
  You → Claude:  tool_result = "Delta Logistics | 3, Eastern Parts | 2"

Step 6 — Claude reads the result and writes the answer
  Claude: "Now I have the data. I can answer."
  Claude → You:  stop_reason = "end_turn"
                 "Delta Logistics has the most overdue invoices with 3..."
```

**The key thing:** Claude never touches your database. Claude only speaks JSON. Your Python is the bridge between Claude and SQLite.

- Claude's job: understand the question → write SQL → interpret results → answer
- Your code's job: carry the SQL to SQLite → carry the result back to Claude

### How your code knows which tool to call

Claude's response contains the tool name as a plain string. Your loop reads it and dispatches:

```python
for block in response.content:
    if block.type == "tool_use":
        tool_name  = block.name   # "query_database" or "search_knowledge_base"
        tool_input = block.input  # {"sql": "..."} or {"query": "..."}
        result = run_tool(tool_name, tool_input)
```

`run_tool` is just a dictionary lookup — string name → Python function:

```python
TOOL_FUNCTIONS = {
    "query_database":        query_database,
    "search_knowledge_base": search_knowledge_base,
}

def run_tool(name, inputs):
    fn = TOOL_FUNCTIONS[name]
    return fn(**inputs)
```

Claude never calls anything directly. It says `"name": "query_database"` as a string. Your code maps that string to the actual function and runs it.

> **Pop Quiz:** "Claude calls query_database but passes the wrong SQL. What do you fix?"
> - A) Rewrite the input_schema
> - B) Improve the tool description with examples of what questions it handles
> - C) Switch to a better model
>
> Answer: B — the description guides Claude's inputs. Add examples of the kinds of questions it should answer and Claude will generate better SQL.

---

## 1:40 — Part 3: Two Tools + Description Quality

> **Key points to land:**
> - The description IS the routing logic — Claude reads it to decide which tool to call
> - Identical vague descriptions = Claude guesses = SQL errors = wrong answer
> - The fix is never the model — it is always the description

### Adding the second tool

One tool answered data questions. But policy questions failed — Claude had nothing to look up.

Add `search_knowledge_base` and now Claude can answer both question types. But how does it know which tool to call?

**The description is the routing logic.** Claude reads the description of each tool and matches it to the question.

```
query_database:        "Use for numbers, counts, amounts, dates, status"
                        → data question → query_database

search_knowledge_base: "Use for policies, procedures, SLAs, guidelines"
                        → policy question → search_knowledge_base
```

Claude does not try both tools. It reads the descriptions and picks one.

### What happens with a bad description

```python
# BAD — identical descriptions, no signal
"description": "Use this tool to look up information and answer questions."

# GOOD — tells Claude exactly when to use it
"description": "Use for numbers, counts, amounts, dates, status.
                Tables: purchase_orders, vendors, invoices, goods_receipt.
                Status values: 'Open', 'Closed', 'Cancelled', 'Paid', 'Overdue', 'Pending'"
```

With bad descriptions:
- Claude has no schema hint → guesses column names → 5-6 SQL errors
- No status hint → uses `due_date < TODAY` instead of `status = 'Overdue'`
- Returns 10 vendors instead of the correct 5

> **Pop Quiz:** "You give Claude two tools but it calls the wrong one. What do you fix?"
> - A) Change the model
> - B) Rewrite the tool description
> - C) Add more tools
>
> Answer: B — the description is the only signal Claude has. Better description = better decisions.

---

## 2:00 — Exercise 3: Two Tools

> **Key points to land:**
> - Part A: Claude routes correctly — point to which tool it called for each question
> - Part B: same tools, same question, broken descriptions — count the retries, see the wrong answer
> - The description is the only thing that changed — that is what caused the failure

**Goal:** add the second tool, then break it to see why descriptions matter.

```bash
python exercises/03-two-tools/exercise_a.py
```

3a — good descriptions. Claude routes every question to the right tool in one call. No retries. Correct answer.

```
Q: Which vendors have overdue invoices?
  → calling tool: query_database(...)

  ← result: vendor_id | name | overdue_count ...

Claude: "5 vendors have overdue invoices..."
```

```bash
python exercises/03-two-tools/exercise_b.py
```

3b — same question, same tools, broken descriptions. Watch what changes:

```
  → calling tool: query_database(...)     ← guesses v.vendor_name

  ← result: Database error: no such column: v.vendor_name

  → calling tool: query_database(...)     ← guesses i.vendor_id

  ← result: Database error: no such column: i.vendor_id

  → calling tool: search_knowledge_base(...)  ← wrong tool entirely

  ← result: [Vendor Payment Policy] ...

  → calling tool: query_database(...)     ← probing schema

  ← result: invoice_id | po_id | amount ...

  → calling tool: query_database(...)     ← finally correct join, wrong WHERE

  ← result: 10 vendors ...               ← wrong answer
```

Same question. Same tools. Same model. Only the descriptions changed.
One line — `"Status values: 'Open', 'Closed', 'Cancelled', 'Paid', 'Overdue', 'Pending'"` — is the difference between 1 call and 5 calls, and between the right answer and the wrong one.

> **Presenter note:** 15 minutes. In 3b, count the retries out loud with the room. Then open tools.py and point to the status hint line.

---

## 2:15 — Part 4: Tool Chaining

> **Key points to land:**
> - Some questions need both tools — Claude calls them in sequence, one result feeds the next
> - The `while` loop is what makes chaining possible — without it you'd get one tool call and stop
> - Claude decides the order dynamically — you never hardcode "call DB first, then KB"

### When one tool is not enough

Some questions need both data AND context:

> "Which vendors have overdue invoices and what does our policy say about handling them?"

This needs:
1. `query_database` — get the overdue vendors
2. `search_knowledge_base` — get the payment policy

Claude calls them in sequence — the result of the first informs the second.

### The loop with two tool calls

```
START
  user_input = "Which vendors have overdue invoices
                AND what does policy say about them?"

  ── ITERATION 1 ──────────────────────────────────────────────
  response = claude.chat(messages, tools)
  # stop_reason = "tool_use"
  # tool_name   = "query_database"
  # tool_inputs = {"sql": "SELECT ... WHERE status = 'Overdue'"}

  result = "Delta Logistics GmbH, Eastern Parts Corp"
  messages.append(tool call + result)

  ── ITERATION 2 ──────────────────────────────────────────────
  response = claude.chat(messages, tools)
  # stop_reason = "tool_use"                ← still not done
  # tool_name   = "search_knowledge_base"   ← now needs policy
  # tool_inputs = {"query": "overdue invoice payment policy"}

  result = "Invoices overdue >90 days must be escalated
            to Finance Director. Vendors with >3 overdue
            invoices flagged for risk review..."
  messages.append(tool call + result)

  ── ITERATION 3 ──────────────────────────────────────────────
  response = claude.chat(messages, tools)
  # stop_reason = "end_turn"                ← now Claude is done
  # content     = "Delta Logistics and Eastern Parts have overdue
  #                invoices. Per policy, escalate to Finance
  #                Director if overdue >90 days."

  print answer
STOP
END
```

Three iterations. Claude orchestrates the sequence dynamically — it decides after each result whether it needs more tools or can now answer.

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

## 2:25 — Exercise 4: Tool Chaining

> **Key points to land:**
> - Count the round trips — 3 iterations for one question
> - Claude called DB first, then KB — you didn't tell it to, it decided
> - You handed it a specific question — the question itself defined the scope

Think of it as a **junior analyst**. You walk up and ask:
> "Which vendors have overdue invoices and what does policy say about them?"

They look up exactly what you asked. Two lookups, one answer. Done. They wait for your next question.

**Goal:** ask questions that need both tools — watch the chain unfold.

```bash
python exercises/04-tool-chaining/exercise.py
```

Step 1: one chained question — watch two tool calls happen in sequence.
Step 2: more examples — different chains for different question types.
Step 3: the loop table — map each step to who acts and what happens.

### How the loop picks which tool to call

After each Claude response your loop scans `response.content` for `tool_use` blocks. Each block has a `name` — that string is how your code knows which function to run:

```python
response.content = [
    ToolUseBlock(
        type  = "tool_use",
        id    = "tool_abc123",
        name  = "query_database",       # ← which tool
        input = {"sql": "SELECT ..."}   # ← what to pass it
    )
]

for block in response.content:
    if block.type == "tool_use":
        result = run_tool(block.name, block.input)
```

`run_tool` maps the name string to the actual Python function:

```python
TOOL_FUNCTIONS = {
    "query_database":        query_database,
    "search_knowledge_base": search_knowledge_base,
}
```

In a chain, this happens twice — once for `query_database`, once for `search_knowledge_base`. Claude decided the order. Your loop just executes whatever name it sees.

### What a ToolUseBlock actually means

This is the LLM's response to your question — but instead of returning text, it's saying:

> "I don't answer this myself — call this tool for me and bring back the result."

The full flow:

```
You → LLM (turn 1 request):
  message = "What is the total sales for Q3?"
  tools   = [query_database schema:
               description: "query the ERP database..."
               tables: purchase_orders, vendors, invoices...
               status values: 'Open', 'Closed', 'Overdue'...]
        ↓
LLM response (turn 1):
  ToolUseBlock(
    name  = "query_database",
    input = {"sql": "SELECT SUM(sales) FROM orders WHERE quarter = 'Q3'"}
  )
  ← NOT an answer. Claude read the table schema and generated the SQL.
     Now it's asking you to run it.
        ↓
Your code runs the SQL → gets back {"total": 94200}
        ↓
You → LLM (turn 2 request):
  ToolResultBlock(tool_use_id="tool_abc123", content="94200")
        ↓
LLM response (turn 2):
  "Total sales for Q3 were $94,200."
  ← NOW it answers.
```

`ToolUseBlock` is never the final answer — it's always a mid-conversation request. The LLM is pausing and delegating. Your code is the one that actually runs the tool. The LLM only sees the result when you send it back.

---

## 2:40 — Part 5: What is an Agent?

> **Key points to land:**
> - Exercises 1-4 built a tool-calling loop — YOU drove it, one question at a time
> - An agent is different: you give it a GOAL, it decides all the steps, it runs until done
> - Same while loop. Same tools. What changes is who drives it — and that changes everything

### The distinction

```
Tool-calling loop (Ex 1-4):
  You ask:  "Which vendors have overdue invoices?"
  Claude:   calls query_database → returns answer
  You ask:  "What does policy say about them?"
  Claude:   calls search_knowledge_base → returns answer
  You drove every step.

Agent (Ex 5):
  You say:  "Audit our procurement health and flag any risks."
  Claude:   decides to check overdue invoices
            decides to check high-risk vendors
            decides to look up relevant policies
            cross-references the findings
            writes a structured report
            stops when the goal is complete
  You drove nothing.
```

### What makes something an agent?

From Anthropic's own definition:

> *"Agents are systems where LLMs dynamically direct their own processes and tool usage, maintaining control over how they accomplish tasks."*

Three things:
- **Autonomous decision-making** — the LLM decides what to do next, not your code
- **Goal-directed** — given a goal, it figures out the steps
- **Environmental feedback** — each result informs the next decision

A simple tool-calling loop where YOU ask each question is NOT an agent. It's a useful building block — but it's you in the loop, not the model.

### What Claude sees — step by step

```
YOU
  │
  │  goal: "Audit procurement health and flag risks."
  │  system: "You are autonomous. Figure out the steps yourself."
  │  tools: [query_database, search_knowledge_base]
  ▼
CLAUDE (iteration 1)
  │
  │  What Claude sees:
  │    - the goal
  │    - two tool descriptions
  │    - no instructions on what order to call them
  │
  │  Claude decides: "I need overdue invoice data first"
  │  stop_reason = "tool_use"
  │  → query_database(sql="SELECT vendor, COUNT(*) ... WHERE status='Overdue'")
  ▼
YOUR CODE runs query_database, sends result back
  ▼
CLAUDE (iteration 2)
  │
  │  What Claude sees:
  │    - the goal (still in context)
  │    - overdue invoice result
  │    - two tool descriptions still available
  │
  │  Claude decides: "now I need high-risk vendor data"
  │  stop_reason = "tool_use"
  │  → query_database(sql="SELECT ... WHERE risk_rating='High'")
  ▼
YOUR CODE runs query_database, sends result back
  ▼
CLAUDE (iteration 3)
  │
  │  Claude decides: "I need policy context now"
  │  stop_reason = "tool_use"
  │  → search_knowledge_base(query="overdue invoice high risk vendor policy")
  ▼
YOUR CODE runs search_knowledge_base, sends result back
  ▼
CLAUDE (iteration 4)
  │
  │  Claude has everything it needs
  │  stop_reason = "end_turn"
  │  → writes structured report
  ▼
YOU get the report
```

**How does Claude know when to stop?** It decides — when it has enough to complete the goal, it returns `end_turn`. You never told it how many steps to take.

### The code barely changes

```python
# Tool-calling loop (Ex 4) — you ask one question
run_agent("Which vendors have overdue invoices?", tools=[...])

# Agent (Ex 5) — you give a goal
run_agent("Audit procurement health and flag risks.", tools=[...])
```

The while loop is identical. The tools are identical. What changes:
1. **System prompt** — "you are autonomous, figure out the steps yourself"
2. **Input** — a goal, not a single question

That's it. The model does the rest.

> **Pop Quiz:** "What is the difference between the loop in Ex 4 and the agent in Ex 5?"
> - A) Different API — agents use a special endpoint
> - B) Different loop — agents have more iterations
> - C) Same loop, different input — goal instead of question, agent decides the steps
>
> Answer: C — the loop is identical. What changed is who drives it.

---

## 2:50 — Exercise 5: The Agent

> **Key points to land:**
> - You gave it one goal — count how many tool calls it made on its own
> - You never told it what to check — it decided
> - The loop is identical to Exercise 4. The system prompt and input changed. That's all.

Think of it as a **senior analyst**. You walk up and say:
> "Audit our procurement health."

They don't ask you what to check. They go off on their own — pull overdue invoices, check high-risk vendors, cross-reference policy, flag anything that looks wrong, write a report. They come back when they're done.

Same database. Same tools. The difference is who decides what to investigate.

**Goal:** give Claude a goal, watch it plan and execute autonomously.

```bash
python exercises/05-agent/exercise.py
```

One goal: *"Audit the procurement health of this organisation."*

Watch the agent:
- Decide what to investigate
- Call tools in whatever order makes sense to it
- Keep going until it has a complete picture
- Write a structured report

You never told it what steps to take.

### Exercise 4 vs Exercise 5

| | Exercise 4 | Exercise 5 |
|---|---|---|
| You give | A specific question | A vague goal |
| Claude does | Answers that question | Decides what to investigate |
| Stops when | Question is answered | It decides the goal is complete |
| Analogy | Junior analyst | Senior analyst |
| Tool calls | Predictable | Varies every run |

---

---

## 3:00 — Part 6: Skills

> **Key points to land:**
> - A skill is a packaged workflow — fixed steps in a SKILL.md file
> - The orchestrator reads all skill descriptions and gives Claude `invoke_skill` as the only tool
> - Claude reads the descriptions and picks — same routing lesson as Exercise 3, one level up
> - The description on SKILL.md is what tells Claude WHEN to call this skill vs another

### What Claude sees — step by step

```
YOU
  │
  │  goal: "Audit the procurement health of this organisation."
  │  tools: [invoke_skill]   ← the ONLY tool Claude gets in phase 1
  ▼
ORCHESTRATOR builds the skill index from .claude/skills/*/SKILL.md:

  "- procurement-audit: Run a full procurement health audit. Use when
     asked to audit procurement, review health, or flag risks."
  "- vendor-deep-dive:  Use when asked about a specific vendor —
     their spend, risk, or invoice history."
  "- spend-report:      Use when asked for a spend summary or Q3 analysis."

  ▼
CLAUDE (routing turn)
  │
  │  What Claude sees:
  │    - the goal
  │    - skill index (name + description for each skill)
  │    - invoke_skill as the only tool
  │
  │  Claude reads descriptions, matches goal to "procurement-audit"
  │  stop_reason = "tool_use"
  │  → invoke_skill(skill="procurement-audit", reason="user asked to audit")
  │
  │  How does Claude pick the right skill?
  │  Same way it picks the right tool in Exercise 3 — it reads the description.
  │  "audit procurement health" matched "Run a full procurement health audit"
  ▼
ORCHESTRATOR loads .claude/skills/procurement-audit/SKILL.md body
Injects it as the system prompt for the next turn
  ▼
CLAUDE (skill execution — same loop as always)
  │
  │  What Claude sees now:
  │    - the goal
  │    - SKILL.md body as the system prompt (fixed instructions)
  │    - query_database + search_knowledge_base as tools
  │
  │  Claude follows the fixed steps from SKILL.md:
  │    step 1 → query_database (overdue invoices)
  │    step 2 → query_database (high-risk vendors)
  │    step 3 → search_knowledge_base (overdue policy)
  │    step 4 → search_knowledge_base (high-risk policy)
  │    step 5 → write structured report
  ▼
YOU get the report — same sections every time
```

### Tool chaining vs Skill — why use a skill at all?

Exercise 4 already chains tools. So why package them into a skill?

```
Tool Chaining (Ex 4):
  Question: "Which vendors are overdue and what does policy say?"

  Run 1:  query_database → search_knowledge_base → answer
  Run 2:  query_database → search_knowledge_base → answer (different structure)
  Run 3:  search_knowledge_base → query_database → answer (different order)

  Claude reasons through the steps fresh every time.
  Output structure varies. Order may vary. You have no control.

Skill (Ex 6):
  Question: "Audit procurement health"

  Run 1:  step1 → step2 → step3 → step4 → report  ← same
  Run 2:  step1 → step2 → step3 → step4 → report  ← same
  Run 3:  step1 → step2 → step3 → step4 → report  ← same

  Claude follows the script you wrote in SKILL.md.
  Same steps. Same output structure. Every time.
```

| | Tool Chaining | Skill |
|---|---|---|
| Steps | Claude decides every run | Fixed by you in SKILL.md |
| Output structure | Varies | Always the same |
| Token cost | Claude reasons about order | No reasoning — just follow steps |
| Use when | Exploration, one-off questions | Production, repeatable workflows |

**Real example:** a weekly procurement report for the CFO. You need the same sections every Monday. Tool chaining might give different sections each run. A skill guarantees the same report every time.

### Agent vs Skill — when to use which

```
Agent (Ex 5):                        Skill (Ex 6):
  You give a goal                      You give a goal
  Claude decides the steps             Steps are fixed in SKILL.md
  Output varies run to run             Output is always the same structure
  Good for: exploration                Good for: production, repeatable workflows
```

### How does Claude know which skill to call when you have 10 skills?

It reads the descriptions — exactly like Exercise 3.

```
Exercise 3:  2 tools,  descriptions route to the right TOOL
Exercise 6:  N skills, descriptions route to the right SKILL
```

Add a new skill → write a SKILL.md with a sharp description → Claude routes to it automatically. No code changes.

> **Pop Quiz:** "You have 10 skills. How does Claude know which one to call?"
> - A) You hardcode the routing logic
> - B) Claude reads the description on each SKILL.md and picks the best match
> - C) It tries all 10 and picks the best result
>
> Answer: B — same as tool descriptions in Exercise 3, one level up.

---

## 3:10 — Exercise 6: Skills

> **Key points to land:**
> - Watch the skill index print — those are the descriptions Claude reads
> - Claude calls `invoke_skill("procurement-audit")` — it matched the description
> - The skill runs fixed steps every time — open SKILL.md and count them
> - Add a new SKILL.md and it appears in the index automatically

**Goal:** same goal as Exercise 5 — watch how skills change the execution.

```bash
python exercises/06-skills/exercise.py
```

> **Presenter note:** 10 minutes. After running, open `.claude/skills/procurement-audit/SKILL.md` and show the fixed steps. Ask: "what would happen if you asked a question about a specific vendor instead?" Answer: Claude would route to a different skill — if you had one with a matching description.

---

## 3:20 — Best Practices

> **Key points to land:**
> - The description is your most important lever — everything else follows from it
> - One tool, one job — don't build swiss-army-knife tools
> - Skills are for repeated chains — don't over-engineer, raw tools first

### Tool description best practices

**1. Be specific about WHEN to use it**

```python
# Bad — Claude doesn't know when to call this
"description": "A useful tool for answering questions"

# Good — Claude knows exactly when
"description": "Use for questions involving numbers, counts, amounts,
dates, or status. Do NOT use for policy or procedure questions."
```

**2. Include the schema in the description**

Claude generates inputs from the description. Give it the table names, column names, and valid values:

```python
"description": """...
Available tables:
  purchase_orders (po_id, vendor_id, material_id, quantity, amount, date, status)
  vendors         (vendor_id, name, country, payment_terms, risk_rating)

Status values: 'Open', 'Closed', 'Cancelled', 'Paid', 'Overdue', 'Pending'"""
```

Without this Claude guesses column names → SQL errors → retries → wrong answer.

**3. Tell Claude what NOT to use it for**

```python
# Prevents Claude calling the skill for simple lookups
"Do NOT use this for simple single-question lookups —
use query_database or search_knowledge_base directly for those."
```

**4. One tool, one job**

Don't build one tool that does everything. Split by responsibility:

```python
# Bad — one tool that does too much
"Use this tool for data questions, policy questions, and report generation"

# Good — three tools, each with a clear job
query_database        → data only
search_knowledge_base → policy only
generate_report       → structured report only
```

### Agent loop best practices

**1. Always check stop_reason**

```python
if response.stop_reason == "tool_use":
    # run the tool
elif response.stop_reason == "end_turn":
    # return the answer
else:
    # handle unexpected stop reason — don't silently ignore it
```

**2. Cap your loop**

Prevent infinite loops with a max iteration count:

```python
MAX_ITERATIONS = 10
iterations = 0

while iterations < MAX_ITERATIONS:
    response = client.messages.create(...)
    iterations += 1
    if response.stop_reason == "end_turn":
        break
```

**3. Return errors to Claude, not exceptions**

When a tool fails, return the error as a string — Claude can read it and recover:

```python
def query_database(sql):
    try:
        # run query
    except Exception as e:
        return f"Database error: {e}"  # Claude sees this and retries
        # NOT: raise e  ← this crashes the loop
```

**4. Keep tool outputs short**

Claude has a context window. Long tool outputs eat into it fast. Cap results:

```python
rows = c.fetchall()
return format_rows(rows[:20])  # cap at 20 rows
```

### Skills best practices

**1. Raw tools first, skills when patterns emerge**

Don't build skills upfront. Run raw chaining, watch what patterns repeat, then package those as skills.

**2. Fix the output format in the skill**

The whole point of a skill is consistency. Use a fixed template:

```python
def generate_report(topic, period):
    spend   = query_database(...)
    overdue = query_database(...)
    policy  = search_knowledge_base(...)
    # fixed sections — always in the same order
    return f"## Top Vendors\n{spend}\n\n## Overdue\n{overdue}\n\n## Policy\n{policy}"
```

**3. Name skills as actions, not objects**

```python
# Bad — sounds like a noun, not clear what it does
"vendor_data"

# Good — clear action
"generate_report", "summarise_spend", "analyse_vendor_risk"
```

---

## 3:15 — Wrap Up

### What you built today

```
data/seed.py               — 50 POs, 10 vendors, 50 invoices, 45 goods receipts
pipeline/knowledge_base.py — 6 procurement policy documents
pipeline/tools.py          — query_database, search_knowledge_base
pipeline/agent.py          — the tool-calling loop: tool call → run → result → loop

Exercise 1 — bare Claude:       sees the failure without tools
Exercise 2 — one tool:          the tool-calling loop in action
Exercise 3 — two tools:         description = routing logic
Exercise 4 — tool chaining:     Claude chains tools dynamically
Exercise 5 — the agent:         give it a goal, it decides all the steps
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
| "What is tool chaining?" | Claude calls multiple tools in sequence, each result informing the next |
| "What is an agent?" | A system where the LLM drives its own process — you give it a goal, it decides the steps |
| "What's the difference between a tool-calling loop and an agent?" | Loop: you ask one question at a time. Agent: you give a goal, it runs autonomously until done |

### Session 2 — What's next

Session 1 built the core tool-calling loop and the agent pattern. Session 2 goes deeper:

```
Session 1 ✓   Tool-calling loop → agent
Session 2     Skills — package repeated chains into a single callable
              Memory — agent remembers across turns
              Reasoning — ReAct: plan, act, observe, repeat
              MCP — expose your agent as an MCP server
```

---
