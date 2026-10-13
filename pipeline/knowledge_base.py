"""
pipeline/knowledge_base.py — internal procurement policy documents.

These are the documents the search_knowledge_base tool searches over.
In production this would be your Confluence, SharePoint, or policy repo.

DOCUMENTS contains procurement policies, vendor SLAs, and process guides.
"""

DOCUMENTS = [
    {
        "id": "doc_001",
        "title": "Vendor Payment Policy",
        "text": """Vendor Payment Policy — Procurement Department

All vendor invoices must be paid within the agreed payment terms stated in the
vendor master record. Standard payment terms are Net 30, Net 45, or Net 60 days.

Late payments incur a penalty of 1.5% per month on the outstanding balance.
Early payment discounts of 2% are available if payment is made within 10 days (2/10 Net 30).

Invoices overdue by more than 90 days must be escalated to the Finance Director.
Vendors with more than 3 overdue invoices in a quarter are flagged for vendor risk review.

All payments above $50,000 require dual approval from the Procurement Manager
and Finance Controller before processing."""
    },
    {
        "id": "doc_002",
        "title": "Vendor Risk Management Policy",
        "text": """Vendor Risk Management Policy

Vendors are classified into three risk tiers:
  Low Risk    — established vendors, >2 years relationship, no compliance issues
  Medium Risk — newer vendors or vendors with minor delivery delays
  High Risk   — vendors with compliance issues, frequent delays, or financial instability

High risk vendors require:
  - Quarterly performance reviews
  - Mandatory on-site audits annually
  - Maximum PO value capped at $25,000 per order
  - Senior procurement manager approval for all orders

Vendors from high-risk countries (as defined by the compliance team) are automatically
assigned Medium or High risk regardless of their track record.

Risk ratings are reviewed quarterly and updated based on delivery performance,
invoice accuracy, and compliance audit results."""
    },
    {
        "id": "doc_003",
        "title": "Three-Way Match Process",
        "text": """Three-Way Match Process — Accounts Payable

Before any invoice is approved for payment, the AP team must perform a three-way match:

  1. Purchase Order (PO)    — what was ordered and at what price
  2. Goods Receipt (GR)     — what was actually delivered
  3. Invoice                — what the vendor is charging

All three must match within a 5% tolerance on quantity and amount.

If the invoice amount exceeds the PO amount by more than 5%, the invoice is
put on hold and the vendor is contacted for a credit note.

If goods receipt quantity is less than invoiced quantity, payment is made only
for the received quantity. The vendor must raise a revised invoice.

Three-way match failures in the last quarter: 12 cases, average resolution time 8 days."""
    },
    {
        "id": "doc_004",
        "title": "Procurement Lead Times by Category",
        "text": """Procurement Lead Times — Category Management

Standard lead times by material category:

  Raw Materials    — 14–21 days (domestic), 30–45 days (international)
  Electronics      — 21–30 days (standard), 45–60 days (custom/configured)
  Packaging        — 7–14 days
  Fasteners        — 5–10 days
  Machinery        — 45–90 days (standard), 90–180 days (custom)

Lead times from German vendors have increased by 15% in Q3 2024 due to
logistics disruptions on the Europe-Asia shipping corridor.

All critical materials (stock level below safety stock) must be ordered with
express shipping regardless of additional cost. Safety stock levels are
defined in the material master."""
    },
    {
        "id": "doc_005",
        "title": "Supplier Onboarding Requirements",
        "text": """Supplier Onboarding Requirements

New vendors must complete the following before receiving a purchase order:

  1. Completed vendor registration form
  2. Valid business registration certificate
  3. Bank account details on company letterhead
  4. ISO 9001 certification (or equivalent quality standard)
  5. Signed code of conduct acknowledgement
  6. Tax compliance certificate (not older than 6 months)

Vendors from outside the EU must also provide:
  - Import/export licence
  - Customs broker details
  - Country of origin certificates for all supplied materials

Onboarding typically takes 10–15 business days.
Expedited onboarding (5 days) is available for critical supply situations
with approval from the Chief Procurement Officer."""
    },
    {
        "id": "doc_006",
        "title": "Spend Analysis Guidelines",
        "text": """Spend Analysis Guidelines — Category Management

Spend analysis is performed quarterly to identify:
  - Top vendors by spend (Pareto — top 20% vendors typically represent 80% of spend)
  - Maverick spend (purchases outside approved vendor list)
  - Category consolidation opportunities
  - Price variance vs standard cost

Key metrics tracked:
  - Total procurement spend by category
  - Spend per vendor
  - Price variance (actual vs standard)
  - Purchase order cycle time (PO creation to goods receipt)
  - Invoice processing time (receipt to payment)

Q3 2024 highlights:
  - Electronics category spend up 23% vs Q2 (new product launch)
  - Raw materials prices stable, within 3% of standard cost
  - Packaging consolidated from 4 vendors to 2, saving 8% on unit costs"""
    },
]
