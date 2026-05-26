import sys
from pathlib import Path
import streamlit as st
from datetime import datetime

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.pipeline import RAGPipeline

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="HDFC MF FAQ Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS (Groww-inspired emerald green accents) ──────────────────────────
st.markdown("""
<style>
    .disclaimer-banner {
        background-color: #fff3cd;
        border: 2px solid #ffc107;
        border-radius: 8px;
        padding: 12px 18px;
        margin-bottom: 18px;
        font-weight: 600;
        color: #7d5a00;
        font-size: 0.95rem;
    }
    .response-card {
        background-color: #f0faf4;
        border-left: 4px solid #00b386;
        border-radius: 6px;
        padding: 16px 20px;
        margin-bottom: 10px;
        color: #1a1a1a;
    }
    .refusal-card {
        background-color: #fff5f5;
        border-left: 4px solid #e53935;
        border-radius: 6px;
        padding: 16px 20px;
        margin-bottom: 10px;
        color: #5c1010;
    }
    .citation-text {
        font-size: 0.82rem;
        color: #007a5e;
        margin-top: 8px;
    }
    .footer-text {
        font-size: 0.78rem;
        color: #888;
        margin-top: 4px;
    }
    .scheme-badge {
        background-color: #00b386;
        color: white;
        border-radius: 12px;
        padding: 2px 12px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 6px;
    }
    .stButton > button {
        border: 1px solid #00b386;
        color: #00b386;
        background: white;
        border-radius: 20px;
        padding: 4px 16px;
        font-size: 0.85rem;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: #00b386;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


# ── Load pipeline (cached across reruns) ──────────────────────────────────────
@st.cache_resource(show_spinner="Loading HDFC FAQ Assistant...")
def load_pipeline():
    return RAGPipeline()


# ── Session state ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "active_scheme" not in st.session_state:
    st.session_state.active_scheme = None
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None


# ── Header ─────────────────────────────────────────────────────────────────────
st.title("📊 HDFC Mutual Fund FAQ Assistant")
st.caption("Powered by Groww data · BGE Hybrid Retrieval · Groq Llama 3")

# ── Fixed disclaimer banner ────────────────────────────────────────────────────
st.markdown(
    '<div class="disclaimer-banner">'
    '⚠️ <b>Facts-only assistant. No investment advice, recommendations, or performance predictions.</b> '
    'All information is sourced from Groww HDFC fund pages for informational purposes only.'
    '</div>',
    unsafe_allow_html=True,
)

# ── Active scheme indicator ────────────────────────────────────────────────────
if st.session_state.active_scheme:
    st.markdown(
        f'<span class="scheme-badge">Active context: {st.session_state.active_scheme}</span>',
        unsafe_allow_html=True,
    )

st.divider()

# ── Example query cards ────────────────────────────────────────────────────────
EXAMPLE_QUERIES = [
    "What is the exit load of HDFC Mid-Cap Fund?",
    "What is the minimum SIP amount for HDFC Small Cap Fund?",
    "What is the benchmark index of HDFC Gold ETF Fund of Fund?",
]

st.markdown("**Quick start — click an example:**")
cols = st.columns(3)
for col, example in zip(cols, EXAMPLE_QUERIES):
    with col:
        if st.button(example, key=f"ex_{example}"):
            st.session_state.pending_query = example

st.divider()

# ── Chat history display ───────────────────────────────────────────────────────
for msg in st.session_state.messages:
    role = msg["role"]
    content = msg["content"]
    meta = msg.get("meta", {})

    if role == "user":
        with st.chat_message("user"):
            st.write(content)
    else:
        with st.chat_message("assistant"):
            if meta.get("blocked"):
                st.markdown(
                    f'<div class="refusal-card">{content}</div>',
                    unsafe_allow_html=True,
                )
            else:
                answer_body = content
                source_url = meta.get("source_url", "")
                last_updated = meta.get("last_updated", "")

                # Strip the Source/Last updated lines from the body (already in meta)
                lines = answer_body.splitlines()
                body_lines = [
                    ln for ln in lines
                    if not ln.strip().startswith("Source:")
                    and not ln.strip().startswith("Last updated from sources:")
                ]
                body = "\n".join(body_lines).strip()

                card_html = f'<div class="response-card">{body}'
                if source_url:
                    card_html += f'<div class="citation-text">📎 <a href="{source_url}" target="_blank">{source_url}</a></div>'
                if last_updated:
                    card_html += f'<div class="footer-text">Last updated from sources: {last_updated}</div>'
                card_html += '</div>'
                st.markdown(card_html, unsafe_allow_html=True)


# ── Process pending query (from example button click) ─────────────────────────
def process_query(query: str, pipeline: RAGPipeline):
    st.session_state.messages.append({"role": "user", "content": query})

    with st.spinner("Searching HDFC fund data..."):
        result = pipeline.run(query)

    meta = {
        "blocked": result["blocked"],
        "block_reason": result.get("block_reason"),
        "source_url": result.get("source_url", ""),
        "scheme_name": result.get("scheme_name", ""),
        "last_updated": result.get("last_updated", ""),
    }

    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "meta": meta,
    })

    if result.get("scheme_name"):
        st.session_state.active_scheme = result["scheme_name"]

    st.rerun()


# ── Handle example button click ────────────────────────────────────────────────
if st.session_state.pending_query:
    query = st.session_state.pending_query
    st.session_state.pending_query = None
    pipeline = load_pipeline()
    process_query(query, pipeline)

# ── Chat input ─────────────────────────────────────────────────────────────────
user_input = st.chat_input("Ask about HDFC mutual fund facts (exit load, SIP, expense ratio, benchmark...)")

if user_input:
    pipeline = load_pipeline()
    process_query(user_input.strip(), pipeline)
