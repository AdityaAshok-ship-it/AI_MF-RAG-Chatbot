# Phase-Wise Implementation Plan: Mutual Fund FAQ Assistant (MFRagChatBot)

This document establishes a concrete, step-by-step roadmap to implement the **Mutual Fund FAQ Assistant (MFRagChatBot)**. The plan is divided into 6 distinct, sequential phases—from initial ingestion of HDFC Mutual Fund data to final Streamlit deployment and evaluation.

---

## 1. Directory Structure Blueprint
To maintain a modular codebase, the project will be laid out as follows:
```
MFRagChatBot/
├── .github/
│   └── workflows/
│       └── daily_ingestion.yml       # Weekday 10 AM IST scheduler
├── docs/
│   ├── context.md                  # Project context & product specs
│   ├── architecture.md             # Technical architecture details
│   └── implementation-plan.md      # This document
├── data/
│   ├── raw/                        # Extracted raw HTML/JSON files from Groww
│   ├── processed/                  # Parsed markdown & chunked JSON files
│   └── document_hashes.json        # Tracker for daily incremental updates
├── src/
│   ├── __init__.py
│   ├── config.py                   # Environment & global configurations
│   ├── ingest/
│   │   ├── __init__.py
│   │   ├── collector.py            # Web scraper/collector for Groww fund pages
│   │   ├── parser.py               # HTML structure & table extractor
│   │   └── chunker.py              # Metadata-rich sliding window chunker
│   ├── database/
│   │   ├── __init__.py
│   │   ├── vector_store.py         # ChromaDB manager (BGE embeddings)
│   │   └── bm25_store.py           # BM25 sparse indexer & persistence
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── hybrid_search.py        # RRF (Dense + Sparse) fusion
│   │   └── reranker.py             # BGE-Reranker-Large integration
│   ├── generation/
│   │   ├── __init__.py
│   │   ├── prompt_templates.py     # Closed-book system prompts
│   │   └── groq_client.py          # Groq Llama 3 connector
│   └── guardrails/
│       ├── __init__.py
│       ├── pii_filter.py           # Regex-based PAN/Aadhaar/bank filter
│       └── advisory_blocker.py     # Intent classifier & refusal templates
├── app/
│   └── main.py                     # Minimalist Streamlit Dashboard
├── tests/
│   ├── test_retrieval.py           # Verification for search recall
│   └── test_guardrails.py          # Verification for PII/Advisory block
├── requirements.txt                # Production dependencies
├── .env.example                    # Template for environment variables
└── README.md                       # High-level overview & setup guide
```

---

## 2. Phase-Wise Implementation Roadmap

### Phase 0: Foundations & Data Ingestion
**Goal:** Establish the environment, extract scheme details from the designated Groww mutual fund URLs, and parse tabular details into structured markdown layouts.
*   **Target Corpus (HDFC Schemes on Groww):**
    1.  `https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth` (Mid Cap)
    2.  `https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth` (Small Cap)
    3.  `https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth` (Gold/Commodity)
    4.  `https://groww.in/mutual-funds/hdfc-multi-cap-fund-direct-growth` (Multi Cap)
    5.  `https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth` (Large Cap)
*   **Step 0.1:** Initialize project virtual environment and structure. Set up `.env` and `src/config.py` including configuration variables:
    ```env
    GROQ_API_KEY=your_groq_api_key_here
    HF_TOKEN=your_huggingface_token_here
    VECTOR_DB_DIR=./data/vector_db
    RAW_DATA_DIR=./data/raw
    PROCESSED_DATA_DIR=./data/processed
    ```
*   **Step 0.2:** Write `collector.py` using BeautifulSoup/Playwright to crawl the 5 designated Groww HDFC URLs and download their raw HTML contents into `data/raw/`. Update `document_hashes.json`.
*   **Step 0.3:** Implement `parser.py` to extract scheme specifics from the Groww HTML pages (Expense Ratio, Exit Load, Minimum SIP, Riskometer level, Benchmark Index, and scheme description) and format the exit load and holdings tables into clean Markdown tables.
*   **Step 0.4:** Write `chunker.py` using `RecursiveCharacterTextSplitter` to create sliding-window chunks (800 tokens, 150 token overlap) tagged with complete metadata:
    `source_url` (matching the Groww links), `document_type` ("Groww Scheme Page"), `scheme_name` (e.g. "HDFC Mid Cap Opportunities Fund"), `page_section` (e.g. "Exit Load & Fees"), `last_updated_date`.
*   **Phase 0 Evaluation:**
    *   *Criterion:* 100% of the 5 targeted Groww HDFC fund pages successfully downloaded and fully parsed.
    *   *Metric:* All tabular arrays (e.g., exit load tables, expense ratio structures) are perfectly preserved in markdown format inside the JSON chunks.

---

### Phase 1: Vector Indexing & Sparse Retrieval Setup
**Goal:** Initialize ChromaDB, generate BGE dense embeddings, build a sparse BM25 index, and create the Reciprocal Rank Fusion (RRF) algorithm.
*   **Step 1.1:** Build `vector_store.py` to load **BAAI/bge-large-en-v1.5** via `SentenceTransformers` and create a persistent ChromaDB instance in `data/vector_db`.
*   **Step 1.2:** Write batch-indexing script that loops through the processed chunks, registers metadata, and upserts dense representations into ChromaDB.
*   **Step 1.3:** Implement `bm25_store.py` utilizing the `rank_bm25` library to build a localized lexical index of the same text chunks. Persist the index using `pickle`.
*   **Step 1.4:** Write `hybrid_search.py` implementing RRF (Reciprocal Rank Fusion):
    $$RRF\_Score(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$
    Where $k = 60$, and $r_m(d)$ is the rank of document $d$ in retriever $m$ (Dense and Sparse).
*   **Phase 1 Evaluation:**
    *   *Criterion:* Retrieval accuracy for key numerical fields.
    *   *Metric:* 100% retrieval recall on standard facts (e.g., querying "HDFC Small Cap exit load" returns the relevant chunk in the top 3 results).

---

### Phase 2: Groq Integration & Basic RAG Pipeline
**Goal:** Connect to the Groq API and design robust prompt templates that enforce short, facts-only answers with citations and source-timestamp footers.
*   **Step 2.1:** Code `groq_client.py` using the official `groq` SDK to send prompt payloads to `llama-3.1-70b-versatile` or `llama-3.3-70b-specdec` with low latency.
*   **Step 2.2:** Design the RAG system prompt in `prompt_templates.py`:
    *   Force model to read **only** the provided chunks.
    *   Enforce a maximum limit of **3 sentences**.
    *   Dictate the mandatory return format including exactly one citation link (the relevant Groww URL) and the update date footer.
*   **Step 2.3:** Write the core pipeline coordinator that connects User Query $\rightarrow$ Hybrid Search $\rightarrow$ Context Construction $\rightarrow$ Groq Completion $\rightarrow$ Citation Validation.
*   **Phase 2 Evaluation:**
    *   *Criterion:* Strict adherence to length boundaries and output formatting.
    *   *Metric:* Less than 5% of responses exceed 3 sentences; all answers contain exactly 1 Groww citation link and the matching footer.

---

### Phase 3: Advanced Retrieval, Reranking & Refusal Guardrails
**Goal:** Implement BGE Reranker-Large, integrate PII security filters, and build comprehensive refusal handling for non-factual or financial advice queries.
*   **Step 3.1:** Integrate **BAAI/bge-reranker-large** in `reranker.py` to re-score the top 10 RRF candidates down to the top 3 highest-quality context chunks.
*   **Step 3.2:** Build `pii_filter.py` incorporating pre-processing regex rules to scrub Aadhaar numbers, PAN cards, phone numbers, and emails.
*   **Step 3.3:** Implement `advisory_blocker.py` using an intent classifier (or custom semantic distance checks) to capture queries requesting direct recommendations ("should I invest in HDFC Mid Cap?", "is HDFC Small Cap better than Large Cap?", "predict gold returns").
*   **Step 3.4:** Map explicit, polite hardcoded refusal templates matching the context requirements (referencing official AMFI educational resources or direct factsheet URLs).
*   **Phase 3 Evaluation:**
    *   *Criterion:* 100% blockade of financial advisory and sensitive privacy breaches.
    *   *Metric:* Zero leaking of mock PII inputs; 100% accurate classification and polite refusal of speculative questions.

---

### Phase 4: GitHub Actions Scheduling Integration
**Goal:** Set up the daily cron scheduler in GitHub Actions to check, download, and index Groww pages for incremental updates.
*   **Step 4.1:** Write `.github/workflows/daily_ingestion.yml` implementing the cron scheduling trigger at `30 4 * * 1-5` (10:00 AM IST on weekdays).
*   **Step 4.2:** Build `scripts/ingest.py` as an entry point that crawls the 5 designated Groww URLs, checks their HTML hashes against `data/document_hashes.json`, and indexes only updated pages.
*   **Step 4.3:** Build `scripts/verify_index.py` to run automated post-indexing checks to guarantee database indexing is intact.
*   **Phase 4 Evaluation:**
    *   *Criterion:* Workflow completes successfully on mock schedules.
    *   *Metric:* Action checks out, caches pip packages, downloads and parses Groww HTML, hashes them, indexes new items, and pushes hash changes without committing credentials.

---

### Phase 5: Streamlit UI Development & End-to-End Evaluation
**Goal:** Build a sleek, minimalist dashboard modeled after Groww, deploy the app, and run RAGAS benchmark evaluations.
*   **Step 5.1:** Create `app/main.py` using **Streamlit**:
    *   Add a prominent, fixed top disclaimer card: *"Facts-only. No investment advice or recommendations."*
    *   Add 3 clickable example cards: (e.g., *"What is the exit load of HDFC Mid-Cap Fund?"*).
    *   Design high-contrast response containers styled with Groww's signature emerald-green borders, clean bold headers, citation links, and timestamps.
*   **Step 5.2:** Set up a testing benchmark utilizing **Ragas** to measure RAG metrics:
    *   **Faithfulness** (relevance of generated response to context chunks).
    *   **Answer Relevancy** (how well the answer covers the user's specific query).
    *   **Context Recall** (whether the system retrieved the necessary chunks to construct the answer).
*   **Step 5.3:** Final end-to-end integration tests, package clean up, and write configuration logs.
*   **Phase 5 Evaluation:**
    *   *Criterion:* RAGAS score thresholds.
    *   *Metric:* **Faithfulness > 0.95**, **Answer Relevancy > 0.90**, **Context Recall > 0.90**. Highly responsive frontend with latencies under 2 seconds.

---

## 3. Comprehensive Summary of Phase Criteria

| Phase | Core Deliverables | Success Metric | Gatekeeper Evaluation |
| :--- | :--- | :--- | :--- |
| **Phase 0** | HTML downloaders, text/table extractor, chunker | 100% extraction accuracy | Groww layout tables render in pure markdown |
| **Phase 1** | BGE ChromaDB indexing, BM25 set up, RRF Fusion | Vector DB search recall | Top 5 RRF returns search targets |
| **Phase 2** | Groq client connector, RAG prompt pipelines | Output constraints | Answers are <= 3 sentences with 1 Groww link |
| **Phase 3** | BGE Reranking, PII Filter, Blocker & Refusals | Safety and compliance | 100% filter rate of PII and advisory |
| **Phase 4** | GitHub Action `.yml` file, incremental hashing | Automated workflow execution | Actions run cron successfully on weekdays |
| **Phase 5** | Groww-styled Streamlit UI, Ragas Evaluation | Interface UX & Ragas scores | Ragas scores > 0.90; responsive UI |
