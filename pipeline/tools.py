"""
pipeline/tools.py — the three tools the agent can call.

Each tool is:
  1. A Python function that does the actual work
  2. A JSON schema that describes it to Claude

Claude reads the schema to decide WHEN to call the tool and WHAT to pass.
The better the description, the better Claude's decisions.

Tools:
  query_database        — run SQL against the ERP database
  search_knowledge_base — semantic search over procurement policy docs
  generate_report       — skill: chains query + search + formats a report
"""

import os
import json
import sqlite3
import warnings
import logging

warnings.filterwarnings("ignore")
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("HF_HUB_VERBOSITY", "error")

DB_PATH = os.path.join(os.path.dirname(__file__), "../data/erp.db")


# ── Tool 1: Query Database ────────────────────────────────────────────────

def query_database(sql: str) -> str:
    """
    Run a read-only SQL query against the ERP database.
    Returns results as a formatted string.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # safety: only allow SELECT
        if not sql.strip().upper().startswith("SELECT"):
            return "Error: only SELECT queries are allowed."

        # make string comparisons case-insensitive
        conn.create_function("UPPER", 1, str.upper)

        c.execute(sql)
        rows = c.fetchall()
        conn.close()

        if not rows:
            return "No results found."

        headers = rows[0].keys()
        lines = [" | ".join(str(h) for h in headers)]
        lines.append("-" * len(lines[0]))
        for row in rows[:20]:  # cap at 20 rows
            lines.append(" | ".join(str(row[h]) for h in headers))

        if len(rows) > 20:
            lines.append(f"... ({len(rows) - 20} more rows)")

        return "\n".join(lines)

    except Exception as e:
        return f"Database error: {e}"


QUERY_DATABASE_SCHEMA = {
    "name": "query_database",
    "description": """Query the ERP procurement database to answer questions about
purchase orders, vendors, invoices, materials, and goods receipts.
Use this for questions involving numbers, counts, amounts, dates, status,
or any data that lives in the database.

Available tables:
  purchase_orders (po_id, vendor_id, material_id, quantity, amount, date, status)
  vendors         (vendor_id, name, country, payment_terms, risk_rating)
  materials       (material_id, name, category, unit_price, stock_level)
  invoices        (invoice_id, po_id, amount, due_date, paid_date, status)
  goods_receipt   (gr_id, po_id, quantity_received, receipt_date)

Always write clean, read-only SELECT statements.
Status values use Title Case: 'Open', 'Closed', 'Cancelled', 'Paid', 'Overdue', 'Pending'.""",
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


# ── Tool 2: Search Knowledge Base ─────────────────────────────────────────

def search_knowledge_base(query: str, top_k: int = 2) -> str:
    """
    Semantic search over internal procurement policy documents.
    Returns the most relevant document chunks.
    """
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        import faiss
        from pipeline.knowledge_base import DOCUMENTS

        encoder = SentenceTransformer("all-MiniLM-L6-v2")

        texts = [f"{d['title']}\n{d['text']}" for d in DOCUMENTS]
        doc_embeddings = encoder.encode(texts, show_progress_bar=False)
        doc_embeddings = np.array(doc_embeddings, dtype="float32")

        index = faiss.IndexFlatIP(doc_embeddings.shape[1])
        faiss.normalize_L2(doc_embeddings)
        index.add(doc_embeddings)

        q_emb = encoder.encode([query], show_progress_bar=False)
        q_emb = np.array(q_emb, dtype="float32")
        faiss.normalize_L2(q_emb)

        scores, indices = index.search(q_emb, top_k)

        results = []
        for i, idx in enumerate(indices[0]):
            doc = DOCUMENTS[idx]
            results.append(f"[{doc['title']}]\n{doc['text'][:500]}...")

        return "\n\n---\n\n".join(results)

    except Exception as e:
        return f"Search error: {e}"


SEARCH_KB_SCHEMA = {
    "name": "search_knowledge_base",
    "description": """Search internal procurement policy documents, guidelines, and process guides.
Use this for questions about policies, rules, procedures, SLAs, lead times,
vendor requirements, or anything that requires explaining HOW things work
rather than showing data from the database.

Examples of when to use this:
  - "What is our payment policy?"
  - "Why are German vendor lead times longer?"
  - "What is the three-way match process?"
  - "What are the onboarding requirements for new vendors?" """,
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language search query"
            }
        },
        "required": ["query"]
    }
}


# ── Tool 3 (Skill): Generate Report ───────────────────────────────────────

def generate_report(topic: str, period: str = "Q3 2024") -> str:
    """
    Skill: generates a structured procurement report by chaining
    query_database and search_knowledge_base internally.
    Returns a formatted report string.
    """
    sections = []

    # Step 1: get spend data
    sql = f"""
        SELECT v.name as vendor, v.country, v.risk_rating,
               COUNT(po.po_id) as total_pos,
               ROUND(SUM(po.amount), 2) as total_spend
        FROM purchase_orders po
        JOIN vendors v ON po.vendor_id = v.vendor_id
        WHERE po.date BETWEEN '2024-07-01' AND '2024-09-30'
        GROUP BY v.vendor_id
        ORDER BY total_spend DESC
        LIMIT 10
    """
    spend_data = query_database(sql)
    sections.append(f"## Top Vendors by Spend — {period}\n\n{spend_data}")

    # Step 2: get overdue invoices
    sql2 = """
        SELECT v.name as vendor, COUNT(i.invoice_id) as overdue_count,
               ROUND(SUM(i.amount), 2) as overdue_amount
        FROM invoices i
        JOIN purchase_orders po ON i.po_id = po.po_id
        JOIN vendors v ON po.vendor_id = v.vendor_id
        WHERE i.status = 'Overdue'
        GROUP BY v.vendor_id
        ORDER BY overdue_count DESC
    """
    overdue_data = query_database(sql2)
    sections.append(f"## Overdue Invoices by Vendor\n\n{overdue_data}")

    # Step 3: get relevant policy context
    policy = search_knowledge_base("vendor payment overdue invoice policy")
    sections.append(f"## Relevant Policy Context\n\n{policy[:400]}...")

    return "\n\n---\n\n".join(sections)


GENERATE_REPORT_SCHEMA = {
    "name": "generate_report",
    "description": """Generate a structured procurement report that combines database data
and policy context. Use this when the user asks for a full report, analysis,
summary, or overview that requires BOTH data AND explanation.

Do NOT use this for simple single-question lookups — use query_database
or search_knowledge_base directly for those.

Examples of when to use this:
  - "Give me a vendor performance report"
  - "Summarise our procurement status for Q3"
  - "I need a full analysis of our top vendors" """,
    "input_schema": {
        "type": "object",
        "properties": {
            "topic": {
                "type": "string",
                "description": "The report topic, e.g. 'vendor performance', 'spend analysis'"
            },
            "period": {
                "type": "string",
                "description": "The time period, e.g. 'Q3 2024'",
                "default": "Q3 2024"
            }
        },
        "required": ["topic"]
    }
}


# ── Tool registry ─────────────────────────────────────────────────────────

TOOL_FUNCTIONS = {
    "query_database":        query_database,
    "search_knowledge_base": search_knowledge_base,
    "generate_report":       generate_report,
}

ALL_TOOLS = [
    QUERY_DATABASE_SCHEMA,
    SEARCH_KB_SCHEMA,
    GENERATE_REPORT_SCHEMA,
]


def run_tool(name: str, inputs: dict) -> str:
    """Dispatch a tool call by name."""
    fn = TOOL_FUNCTIONS.get(name)
    if not fn:
        return f"Unknown tool: {name}"
    return fn(**inputs)
