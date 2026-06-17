# HDFC Mutual Fund FAQ Assistant

A facts-only RAG chatbot that answers questions about 5 HDFC mutual fund schemes using data scraped from Groww. It refuses investment advice, blocks PII, and cites every answer with the exact Groww source URL.

---

## What it does

- Answers factual queries about expense ratios, exit loads, minimum SIP amounts, benchmark indices, riskometer classifications, and asset allocations
- Blocks advisory/speculative questions ("should I invest in…") with a standardised SEBI-compliant refusal
- Strips PII (PAN, Aadhaar, phone, email) from queries before any processing
- Every answer is grounded in retrieved chunks and capped at 3 sentences + one citation link + a "Last updated" footer

## Covered schemes

| Scheme | Groww URL |
|--------|-----------|
| HDFC Mid-Cap Opportunities Fund (Direct – Growth) | `groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth` |
| HDFC Small Cap Fund (Direct – Growth) | `groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth` |
| HDFC Gold ETF Fund of Fund (Direct – Growth) | `groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth` |
| HDFC Multi-Cap Fund (Direct – Growth) | `groww.in/mutual-funds/hdfc-multi-cap-fund-direct-growth` |
| HDFC Large-Cap Fund (Direct – Growth) | `groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth` |

---

## Architecture

```
User query
    │
    ▼
Guardrails (PII filter → Advisory blocker)
    │
    ▼
Hybrid Search
    ├── Dense: ChromaDB (BAAI/bge-large-en-v1.5 embeddings)
    └── Sparse: BM25 (rank_bm25)
    │
    ▼
Reciprocal Rank Fusion → BGE Reranker (top 3 chunks)
    │
    ▼
Groq API — Llama 3 (closed-book, context-only)
    │
    ▼
Streamlit UI (response card + citation + footer)
```

The corpus is refreshed automatically via **GitHub Actions** every weekday at 10:00 AM IST. The scraper compares MD5 hashes of each fund page and only re-indexes pages that have changed.

---

## Project structure

```
.
├── app/
│   └── main.py               # Streamlit UI
├── src/
│   ├── config.py             # Paths, model names, URLs
│   ├── pipeline.py           # End-to-end RAG orchestration
│   ├── ingest/
│   │   ├── collector.py      # Groww HTML scraper (hash-diff aware)
│   │   ├── parser.py         # BeautifulSoup → Markdown
│   │   └── chunker.py        # Recursive chunker (800 tok / 150 overlap)
│   ├── database/
│   │   ├── vector_store.py   # ChromaDB wrapper
│   │   └── bm25_store.py     # BM25 index (rank_bm25)
│   ├── retrieval/
│   │   ├── hybrid_search.py  # RRF fusion of dense + sparse
│   │   └── reranker.py       # BAAI/bge-reranker-large
│   ├── generation/
│   │   ├── groq_client.py    # Groq API wrapper with retry
│   │   └── prompt_templates.py
│   └── guardrails/
│       ├── pii_filter.py     # Regex-based PII detection
│       └── advisory_blocker.py
├── scripts/
│   ├── ingest.py             # Run the full ingestion pipeline
│   └── verify_index.py       # Golden-query smoke tests against the index
├── data/
│   ├── raw/                  # Scraped HTML files
│   ├── processed/            # Parsed Markdown + JSON per scheme
│   ├── vector_db/            # ChromaDB persistent store
│   └── document_hashes.json  # Per-scheme MD5 hashes (committed, tracked by CI)
├── tests/
│   ├── test_guardrails.py
│   └── test_retrieval.py
├── docs/                     # Architecture, context, edge cases, eval plan
├── .github/workflows/
│   └── daily_ingestion.yml   # Weekday 10 AM IST auto-ingest
├── .env.example
└── requirements.txt
```

---

## Local setup

**Prerequisites:** Python 3.10+

```bash
# 1. Clone and enter the repo
git clone <repo-url>
cd MFRagChatBot

# 2. Create a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env — fill in GROQ_API_KEY and optionally HF_TOKEN
```

### Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes | API key from [console.groq.com](https://console.groq.com) |
| `HF_TOKEN` | No | HuggingFace token (only needed if models are gated) |

---

## Running

### Step 1 — Populate the index (first run only)

```bash
python scripts/ingest.py
```

This scrapes the 5 Groww fund pages, parses them into chunks, embeds with `BAAI/bge-large-en-v1.5`, and writes to `data/vector_db/` and `data/processed/`.

The first run also downloads the embedding and reranker models (~1.5 GB total) from HuggingFace.

### Step 2 — Verify the index

```bash
python scripts/verify_index.py
```

Runs 5 golden queries against the index and exits with code 1 if any fail.

### Step 3 — Start the app

```bash
streamlit run app/main.py
```

---

## Automated ingestion (GitHub Actions)

The workflow at `.github/workflows/daily_ingestion.yml` runs every weekday at **10:00 AM IST** (04:30 AM UTC). It:

1. Checks out the repo
2. Installs dependencies from `requirements.txt`
3. Runs `scripts/ingest.py` (skips unchanged fund pages via hash comparison)
4. Runs `scripts/verify_index.py` (fails the workflow if golden queries regress)
5. Commits updated `data/document_hashes.json` back to the repo if any pages changed

**Required GitHub repository secrets:**

| Secret | Purpose |
|--------|---------|
| `GROQ_API_KEY` | LLM inference during verify step |
| `HF_TOKEN` | HuggingFace model download (if needed) |

To trigger manually: go to **Actions → Daily Mutual Fund Corpus Ingestion → Run workflow**.

---

## Models used

| Model | Role | Size |
|-------|------|------|
| `BAAI/bge-large-en-v1.5` | Query + document embeddings | 1024-dim |
| `BAAI/bge-reranker-large` | Cross-encoder reranking | ~1.3 GB |
| `llama-3.1-70b-versatile` (Groq) | Answer generation | Hosted API |

---

## Guardrails

| Guard | Trigger | Behaviour |
|-------|---------|-----------|
| PII filter | PAN, Aadhaar, phone, email in query | Refuse, log, never send to LLM |
| Advisory blocker | "should I invest", "which is better", return queries | Refuse with AMFI education link |
| No-context fallback | Retrieval returns zero results | Static refusal message |
| Citation validator | LLM response missing Groww URL | Appends citation from chunk metadata |

---

## Running tests

```bash
pytest tests/
```
