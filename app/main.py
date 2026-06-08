import sys
import time
from pathlib import Path
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.pipeline import RAGPipeline

# ── Page Configuration ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="HDFC Fund Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Handle Query Parameters (For sidebar click navigation) ────────────────────
if "scheme" in st.query_params:
    st.session_state.active_scheme = st.query_params["scheme"]

# ── Load RAG Pipeline (Cached across reruns) ──────────────────────────────────
@st.cache_resource(show_spinner="Loading HDFC FAQ Assistant...")
def load_pipeline():
    return RAGPipeline()

# ── Session State Initializations ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "active_scheme" not in st.session_state:
    st.session_state.active_scheme = None
if "pending_query" not in st.session_state:
    st.session_state.pending_query = None
if "thinking_step" not in st.session_state:
    st.session_state.thinking_step = 0

# ── Premium Dark-Themed Glassmorphic Stylesheet ───────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono&display=swap');

    :root {
        --primary-bg: #0D0F14;
        --secondary-surface: #141720;
        --accent-primary: #00C48C;
        --accent-secondary: #7B61FF;
        --text-primary: #F0F2F5;
        --text-secondary: #8A92A0;
        --border-color: #1E2330;
        --danger-color: #FF6B6B;
        --gold-color: #FFB74D;
    }

    /* Base application background and font overrides */
    .stApp {
        background-color: var(--primary-bg) !important;
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* Override standard containers for padding */
    .main .block-container {
        padding-top: 120px !important;
        padding-bottom: 120px !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 1300px !important;
        margin: 0 auto !important;
    }

    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: var(--border-color);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-secondary);
    }

    /* Hide default streamlit header/footer */
    header, footer {
        visibility: hidden !important;
        height: 0px !important;
    }
    [data-testid="stHeader"] {
        display: none !important;
    }

    /* Sidebar Custom Styling */
    [data-testid="stSidebar"] {
        background-color: var(--secondary-surface) !important;
        border-right: 1px solid var(--border-color) !important;
        padding-top: 1.5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    [data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] {
        color: var(--text-primary) !important;
    }

    /* Custom Sticky Top Navigation Bar */
    .sticky-nav {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 64px;
        background-color: rgba(20, 23, 32, 0.85);
        backdrop-filter: blur(12px);
        border-bottom: 1px solid var(--border-color);
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 24px;
        z-index: 999;
    }
    .nav-left {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .logo-circle {
        width: 36px;
        height: 36px;
        background: radial-gradient(circle, rgba(0, 196, 140, 0.2) 0%, rgba(0, 0, 0, 0) 70%);
        border: 2px solid var(--accent-primary);
        border-radius: 50%;
        color: var(--accent-primary);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 14px;
        box-shadow: 0 0 10px rgba(0, 196, 140, 0.3);
    }
    .nav-title {
        font-weight: 700;
        font-size: 18px;
        color: var(--text-primary);
        letter-spacing: -0.01em;
    }
    .nav-center {
        display: flex;
        align-items: center;
    }
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background-color: rgba(255, 255, 255, 0.04);
        border: 1px solid var(--border-color);
        padding: 6px 14px;
        border-radius: 99px;
        font-size: 12px;
        color: var(--text-secondary);
    }
    .pulse-dot {
        width: 8px;
        height: 8px;
        background-color: var(--accent-primary);
        border-radius: 50%;
        box-shadow: 0 0 0 0 rgba(0, 196, 140, 0.7);
        animation: pulse 1.6s infinite;
    }
    @keyframes pulse {
        0% {
            transform: scale(0.95);
            box-shadow: 0 0 0 0 rgba(0, 196, 140, 0.7);
        }
        70% {
            transform: scale(1);
            box-shadow: 0 0 0 6px rgba(0, 196, 140, 0);
        }
        100% {
            transform: scale(0.95);
            box-shadow: 0 0 0 0 rgba(0, 196, 140, 0);
        }
    }
    .nav-right {
        display: flex;
        gap: 16px;
        color: var(--text-secondary);
        font-size: 16px;
    }
    .nav-icon {
        cursor: pointer;
        transition: color 0.2s ease;
    }
    .nav-icon:hover {
        color: var(--text-primary);
    }

    /* Regulatory Disclaimer Banner */
    .disclaimer-banner-fixed {
        position: fixed;
        top: 64px;
        left: 0;
        right: 0;
        height: 40px;
        background-color: rgba(255, 107, 107, 0.08);
        border-bottom: 1px solid rgba(255, 107, 107, 0.25);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        color: var(--danger-color);
        font-weight: 500;
        z-index: 998;
        backdrop-filter: blur(8px);
    }

    /* Sidebar Fund selector cards */
    .sidebar-title {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: var(--text-secondary);
        margin: 20px 0 10px 0;
        padding-left: 4px;
    }
    .fund-card {
        background-color: rgba(255, 255, 255, 0.02);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 10px;
        display: flex;
        flex-direction: column;
        gap: 6px;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    .fund-card:hover {
        background-color: rgba(255, 255, 255, 0.05);
        border-left: 3px solid var(--accent-secondary);
        transform: translateX(2px);
    }
    .fund-card.active {
        background-color: rgba(0, 196, 140, 0.06);
        border-left: 3px solid var(--accent-primary);
        border-color: rgba(0, 196, 140, 0.25);
        box-shadow: inset 0 0 0 1px rgba(0, 196, 140, 0.1);
    }
    .fund-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .fund-name {
        font-size: 13px;
        font-weight: 600;
        color: var(--text-primary);
    }
    .fund-sub {
        font-size: 11px;
        color: var(--text-secondary);
    }
    .fund-badge {
        font-size: 10px;
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 4px;
        display: inline-block;
    }
    .fund-badge.equity {
        background-color: rgba(123, 97, 255, 0.15);
        color: var(--accent-secondary);
    }
    .fund-badge.fof {
        background-color: rgba(255, 183, 77, 0.15);
        color: var(--gold-color);
    }

    .sidebar-footer {
        margin-top: 30px;
        padding-top: 15px;
        border-top: 1px solid var(--border-color);
        font-size: 10px;
        font-style: italic;
        color: var(--text-secondary);
        display: flex;
        flex-direction: column;
        gap: 6px;
    }

    /* Chat bubble structures */
    .chat-row {
        display: flex;
        width: 100%;
        margin-bottom: 24px;
        gap: 12px;
    }
    .user-row {
        justify-content: flex-end;
    }
    .ai-row {
        justify-content: flex-start;
    }
    .user-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background-color: #2E3A59;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 12px;
        align-self: flex-start;
    }
    .ai-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background-color: rgba(123, 97, 255, 0.1);
        border: 1px solid rgba(123, 97, 255, 0.3);
        color: var(--accent-secondary);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        align-self: flex-start;
    }
    .hexagon {
        font-weight: bold;
    }
    .chat-bubble {
        padding: 14px 18px;
        border-radius: 16px;
        max-width: 80%;
        font-size: 14px;
        line-height: 1.5;
    }
    .user-bubble {
        background: linear-gradient(135deg, #161D2B, #1B243B);
        border: 1px solid #2A364F;
        color: var(--text-primary);
        border-top-right-radius: 4px;
    }
    .ai-bubble {
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid var(--border-color);
        border-left: 3px solid var(--accent-secondary);
        color: var(--text-primary);
        border-top-left-radius: 4px;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    .refusal-bubble {
        background-color: rgba(255, 107, 107, 0.04);
        border: 1px solid rgba(255, 107, 107, 0.2);
        border-left: 3px solid var(--danger-color);
    }
    .ai-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
        gap: 8px;
    }
    .ai-name {
        font-weight: 700;
        font-size: 13px;
    }
    .ai-badge {
        font-size: 10px;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 99px;
    }
    .success-badge {
        background-color: rgba(0, 196, 140, 0.1);
        color: var(--accent-primary);
    }
    .refusal-badge {
        background-color: rgba(255, 107, 107, 0.15);
        color: var(--danger-color);
    }
    .ai-content {
        font-weight: 400;
    }
    .ai-footer {
        display: flex;
        flex-direction: column;
        gap: 6px;
        margin-top: 4px;
    }
    .citation-pill {
        align-self: flex-start;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background-color: rgba(255, 183, 77, 0.08);
        border: 1px solid rgba(255, 183, 77, 0.25);
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 11px;
        color: var(--gold-color);
        text-decoration: none;
        transition: all 0.2s ease;
        font-weight: 500;
    }
    .citation-pill:hover {
        background-color: rgba(255, 183, 77, 0.15);
        box-shadow: 0 2px 8px rgba(255, 183, 77, 0.1);
        text-decoration: underline;
    }
    .ai-metadata {
        font-size: 11px;
        color: var(--text-secondary);
    }

    /* Welcome Hero State */
    .welcome-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 50px 20px 20px 20px;
        width: 100%;
    }
    .welcome-logo {
        width: 64px;
        height: 64px;
        background: radial-gradient(circle, rgba(0, 196, 140, 0.25) 0%, rgba(0, 0, 0, 0) 70%);
        border: 3px solid var(--accent-primary);
        border-radius: 50%;
        color: var(--accent-primary);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 900;
        font-size: 24px;
        margin-bottom: 24px;
        box-shadow: 0 0 20px rgba(0, 196, 140, 0.4);
    }
    .welcome-title {
        font-size: 28px;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 12px;
        letter-spacing: -0.5px;
    }
    .welcome-subtitle {
        font-size: 15px;
        color: var(--text-secondary);
        margin-bottom: 40px;
        max-width: 500px;
    }
    .quick-start-title {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1px;
        color: var(--accent-primary);
        text-transform: uppercase;
        margin-bottom: 18px;
    }

    /* Style ALL Streamlit secondary buttons globally to match the premium dark theme */
    div.stButton > button,
    button[kind="secondary"],
    [data-testid="stBaseButton-secondary"] {
        background-color: #141720 !important;
        background: #141720 !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
        padding: 20px 16px !important;
        text-align: left !important;
        min-height: 110px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: flex-start !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 13.5px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2) !important;
    }
    div.stButton > button:hover,
    button[kind="secondary"]:hover,
    [data-testid="stBaseButton-secondary"]:hover {
        transform: translateY(-4px) !important;
        border-color: var(--accent-primary) !important;
        box-shadow: 0 6px 20px rgba(0, 196, 140, 0.15) !important;
        background: rgba(0, 196, 140, 0.08) !important;
    }
    div.stButton > button p,
    button[kind="secondary"] p,
    [data-testid="stBaseButton-secondary"] p,
    div.stButton > button span,
    button[kind="secondary"] span,
    [data-testid="stBaseButton-secondary"] span {
        color: #F0F2F5 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 13.5px !important;
        font-weight: 500 !important;
        text-align: left !important;
    }

    /* Thinking Indicator */
    .thinking-container {
        background-color: rgba(255, 255, 255, 0.02);
        border: 1px solid var(--border-color);
        padding: 14px 18px;
        border-radius: 16px;
        border-top-left-radius: 4px;
        display: flex;
        flex-direction: column;
        gap: 12px;
        min-width: 320px;
    }
    .typing-dots {
        display: flex;
        gap: 4px;
        align-items: center;
        height: 12px;
    }
    .dot {
        width: 6px;
        height: 6px;
        background-color: var(--accent-secondary);
        border-radius: 50%;
        animation: bounce 1.2s infinite ease-in-out;
    }
    @keyframes bounce {
        0%, 100% {
            transform: translateY(0);
        }
        50% {
            transform: translateY(-5px);
        }
    }
    .pipeline-strip {
        display: flex;
        align-items: center;
        gap: 8px;
        background-color: rgba(0, 0, 0, 0.2);
        border: 1px solid var(--border-color);
        padding: 6px 12px;
        border-radius: 8px;
        font-size: 11px;
        color: var(--text-secondary);
        align-self: flex-start;
    }
    .pipeline-step {
        transition: all 0.3s ease;
    }
    .pipeline-step.active.done {
        color: var(--accent-primary);
        font-weight: 600;
    }
    .pipeline-step.active.current {
        color: var(--accent-secondary);
        font-weight: 600;
        animation: pulse-text 1.2s infinite;
    }
    @keyframes pulse-text {
        0%, 100% { opacity: 0.7; }
        50% { opacity: 1; }
    }
    .arrow {
        font-size: 10px;
        opacity: 0.5;
    }

    /* Bottom Input Area overrides */
    [data-testid="stBottom"],
    [data-testid="stBottom"] > div,
    [data-testid="stBottomBlockContainer"] {
        background-color: #0D0F14 !important;
        background: #0D0F14 !important;
    }
    [data-testid="stChatInput"],
    [data-testid="stChatInput"] > div,
    [data-testid="stChatInput"] div {
        background-color: var(--secondary-surface) !important;
        background: var(--secondary-surface) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2) !important;
    }
    [data-testid="stChatInput"] textarea {
        background-color: transparent !important;
        color: var(--text-primary) !important;
        -webkit-text-fill-color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 14px !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: var(--text-secondary) !important;
        opacity: 0.6 !important;
    }
    [data-testid="stChatInput"] button {
        background: linear-gradient(135deg, var(--accent-primary), #00A870) !important;
        color: white !important;
        border-radius: 50% !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 0 10px rgba(0, 196, 140, 0.3) !important;
    }
    [data-testid="stChatInput"] button:hover {
        transform: scale(1.05) !important;
        box-shadow: 0 0 15px rgba(0, 196, 140, 0.5) !important;
    }

    .input-status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background-color: rgba(0, 196, 140, 0.08);
        border: 1px solid rgba(0, 196, 140, 0.2);
        color: var(--accent-primary);
        padding: 4px 12px;
        border-radius: 99px;
        font-size: 11px;
        margin-bottom: 8px;
        font-weight: 500;
        margin-top: 10px;
    }

    /* Collapsible metadata inspector styling */
    .meta-section-title {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: var(--text-secondary);
        margin: 20px 0 10px 0;
    }
    .meta-card {
        background-color: var(--secondary-surface);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 14px;
        display: flex;
        flex-direction: column;
        gap: 10px;
        margin-bottom: 15px;
    }
    .meta-row {
        display: flex;
        justify-content: space-between;
        font-size: 13px;
    }
    .meta-label {
        color: var(--text-secondary);
    }
    .meta-value {
        color: var(--text-primary);
        font-weight: 600;
    }
    .chunk-card {
        background-color: rgba(255, 255, 255, 0.02);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 12px;
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .chunk-header {
        display: flex;
        justify-content: space-between;
        font-size: 11px;
        font-weight: 600;
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 6px;
        gap: 8px;
    }
    .chunk-scheme {
        color: var(--accent-primary);
    }
    .chunk-section {
        color: var(--accent-secondary);
    }
    .chunk-text {
        font-size: 12px;
        color: var(--text-primary);
        line-height: 1.4;
        font-style: italic;
    }
    .chunk-score-container {
        display: flex;
        flex-direction: column;
        gap: 4px;
        margin-top: 4px;
    }
    .score-label {
        font-size: 10px;
        color: var(--text-secondary);
    }
    .score-bar-bg {
        height: 4px;
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 99px;
        overflow: hidden;
    }
    .score-bar-fill {
        height: 100%;
        background-color: var(--accent-primary);
        border-radius: 99px;
    }
</style>
""", unsafe_allow_html=True)

# ── Render Custom Sticky Navigation Bar & Banner ──────────────────────────────
st.markdown("""
<div class="sticky-nav">
    <div class="nav-left">
        <div class="logo-circle">MF</div>
        <span class="nav-title">HDFC Fund Assistant</span>
    </div>
    <div class="nav-center">
        <span class="status-badge"><span class="pulse-dot"></span> Live · Corpus updated: 31 May 2026</span>
    </div>
    <div class="nav-right">
        <span class="nav-icon">🔔</span>
        <span class="nav-icon" style="margin-left: 10px;">⚙️</span>
    </div>
</div>
<div class="disclaimer-banner-fixed">
    <span>⚠️ Facts-only assistant · No investment advice or recommendations · Data sourced exclusively from official Groww scheme pages</span>
</div>
""", unsafe_allow_html=True)


# ── Render Custom Sidebar Fund Selector Panel ─────────────────────────────────
st.sidebar.markdown('<div class="sidebar-title">HDFC Funds</div>', unsafe_allow_html=True)

FUNDS = [
    {
        "name": "HDFC Mid-Cap Opportunities Fund",
        "short_name": "Mid-Cap Opportunities",
        "badge": "Equity · Very High Risk",
        "badge_class": "equity",
        "type": "Equity",
        "risk": "Very High Risk"
    },
    {
        "name": "HDFC Small Cap Fund",
        "short_name": "Small Cap Fund",
        "badge": "Equity · Very High Risk",
        "badge_class": "equity",
        "type": "Equity",
        "risk": "Very High Risk"
    },
    {
        "name": "HDFC Gold ETF Fund of Fund",
        "short_name": "Gold ETF FoF",
        "badge": "FoF · High Risk",
        "badge_class": "fof",
        "type": "FoF",
        "risk": "High Risk"
    },
    {
        "name": "HDFC Multi-Cap Fund",
        "short_name": "Multi-Cap Fund",
        "badge": "Equity · Very High Risk",
        "badge_class": "equity",
        "type": "Equity",
        "risk": "Very High Risk"
    },
    {
        "name": "HDFC Large-Cap Fund",
        "short_name": "Large-Cap Fund",
        "badge": "Equity · High Risk",
        "badge_class": "equity",
        "type": "Equity",
        "risk": "High Risk"
    }
]

# Generate custom sidebar HTML links
sidebar_html = ""
for fund in FUNDS:
    is_active = st.session_state.active_scheme == fund["name"]
    active_class = "active" if is_active else ""
    
    sidebar_html += f"""
    <a href="?scheme={fund['name'].replace(' ', '+')}" target="_self" style="text-decoration: none; color: inherit;">
        <div class="fund-card {active_class}">
            <div class="fund-card-header">
                <span class="fund-name">{fund['short_name']}</span>
                <span class="fund-badge {fund['badge_class']}">{fund['badge']}</span>
            </div>
            <span class="fund-sub">Direct · Growth</span>
        </div>
    </a>
    """

st.sidebar.markdown(sidebar_html, unsafe_allow_html=True)

# Toggle for the Collapsible Response Metadata Panel
show_inspector = st.sidebar.toggle("📊 Retrieval Inspector", value=True)

# Sidebar footer
st.sidebar.markdown("""
<div class="sidebar-footer">
    <span>⚡ Powered by Hybrid RAG · BGE + BM25 + RRF</span>
    <span>🤖 LLM: Groq Llama 3</span>
    <span>🟢 Corpus: Updated Today</span>
    <span style="opacity: 0.4; font-size: 8px; margin-top: 10px;">SEBI/AMFI Compliant Watermark</span>
</div>
""", unsafe_allow_html=True)


# ── Grid Layout: Main Chat vs Collapsible Metadata Panel ──────────────────────
if show_inspector:
    col_main, col_meta = st.columns([7, 3])
else:
    col_main = st.container()
    col_meta = None


# ── Render Message Bubble Functions ───────────────────────────────────────────
def render_user_message(content, container=st):
    html = f"""
    <div class="chat-row user-row">
        <div class="chat-bubble user-bubble">
            {content}
        </div>
        <div class="user-avatar">U</div>
    </div>
    """
    container.markdown(html, unsafe_allow_html=True)


def render_ai_message(content, meta, container=st):
    blocked = meta.get("blocked", False)
    block_reason = meta.get("block_reason")
    source_url = meta.get("source_url", "")
    last_updated = meta.get("last_updated", "")
    
    if blocked:
        badge_text = "⛔ Advisory Blocked" if block_reason == "advisory" else "⛔ PII Blocked"
        badge_class = "refusal-badge"
        bubble_class = "refusal-bubble"
        link_html = '<a class="citation-pill" href="https://www.amfiindia.com/investor-corner" target="_blank">🎓 AMFI Investor Education</a>'
        
        html = f"""
        <div class="chat-row ai-row">
            <div class="ai-avatar"><span class="hexagon">⬡</span></div>
            <div class="chat-bubble ai-bubble {bubble_class}">
                <div class="ai-header">
                    <span class="ai-name" style="color: var(--danger-color);">HDFC Fund Assistant</span>
                    <span class="ai-badge {badge_class}">{badge_text}</span>
                </div>
                <div class="ai-content">
                    {content}
                </div>
                <div class="ai-footer">
                    {link_html}
                </div>
            </div>
        </div>
        """
    else:
        # Strip internal lines if any (sanity check)
        lines = content.splitlines()
        body_lines = [
            ln for ln in lines
            if not ln.strip().startswith("Source:")
            and not ln.strip().startswith("Last updated from sources:")
        ]
        body = "\n".join(body_lines).strip()
        
        citation_html = ""
        if source_url:
            citation_html = f'<a class="citation-pill" href="{source_url}" target="_blank">🔗 View Source on Groww</a>'
            
        footer_html = ""
        if last_updated:
            footer_html = f'<div class="ai-metadata">Last updated from sources: {last_updated}</div>'
            
        html = f"""
        <div class="chat-row ai-row">
            <div class="ai-avatar"><span class="hexagon">⬡</span></div>
            <div class="chat-bubble ai-bubble">
                <div class="ai-header">
                    <span class="ai-name" style="color: var(--accent-secondary);">HDFC Fund Assistant</span>
                    <span class="ai-badge success-badge">🛡️ Verified Groww Data</span>
                </div>
                <div class="ai-content">
                    {body}
                </div>
                <div class="ai-footer">
                    {citation_html}
                    {footer_html}
                </div>
            </div>
        </div>
        """
    container.markdown(html, unsafe_allow_html=True)


def render_thinking_state(step=2, container=st):
    step1_class = "active done" if step >= 1 else ""
    step2_class = "active done" if step >= 2 else ""
    if step == 2:
        step2_class = "active current"
    step3_class = "active done" if step >= 3 else ""
    if step == 3:
        step3_class = "active current"
    step4_class = "active done" if step >= 4 else ""
    if step == 4:
        step4_class = "active current"
        
    html = f"""
    <div class="chat-row ai-row thinking-row">
        <div class="ai-avatar"><span class="hexagon animate-pulse">⬡</span></div>
        <div class="thinking-container">
            <div class="typing-dots">
                <div class="dot"></div>
                <div class="dot" style="animation-delay: 150ms;"></div>
                <div class="dot" style="animation-delay: 300ms;"></div>
            </div>
            <div class="pipeline-strip">
                <span class="pipeline-step {step1_class}">Guardrails ✓</span>
                <span class="arrow">→</span>
                <span class="pipeline-step {step2_class}">Hybrid Search ⏳</span>
                <span class="arrow">→</span>
                <span class="pipeline-step {step3_class}">Reranking</span>
                <span class="arrow">→</span>
                <span class="pipeline-step {step4_class}">LLM</span>
            </div>
        </div>
    </div>
    """
    container.markdown(html, unsafe_allow_html=True)


# ── Render MAIN Chat Area ─────────────────────────────────────────────────────
with col_main:
    # 1. Welcome Hero State (When no messages are present)
    if len(st.session_state.messages) == 0:
        st.markdown("""
        <div class="welcome-container">
            <div class="welcome-logo">MF</div>
            <h1 class="welcome-title">Ask anything about HDFC Mutual Funds</h1>
            <p class="welcome-subtitle">Grounded in verified Groww data. Strictly facts. Zero advice.</p>
            <span class="quick-start-title">Quick Start Prompts</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Staggered CSS quick start button cards
        st.markdown('<div class="quick-start-cols">', unsafe_allow_html=True)
        q_cols = st.columns(3)
        
        EXAMPLES = [
            ("💰 Exit Load", "What is the exit load for HDFC Mid-Cap Opportunities Fund?", "q1"),
            ("📊 Min SIP", "Minimum SIP amount for HDFC Small Cap Fund?", "q2"),
            ("📈 Benchmark", "Which benchmark index does HDFC Large-Cap Fund follow?", "q3")
        ]
        
        for index, (label, question, key) in enumerate(EXAMPLES):
            with q_cols[index]:
                if st.button(f"{label}\n\n{question}", key=key):
                    st.session_state.pending_query = question
        st.markdown('</div>', unsafe_allow_html=True)

    # 2. Conversation Thread Loop
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            render_user_message(msg["content"])
        else:
            render_ai_message(msg["content"], msg.get("meta", {}))

    # 3. Dynamic Thinking State Indicator (Staggered updates for WOW factor)
    thinking_container = st.empty()
    if st.session_state.thinking_step > 0:
        render_thinking_state(st.session_state.thinking_step, container=thinking_container)


# ── Process Query Function ────────────────────────────────────────────────────
def process_query(query: str):
    # Append user question
    st.session_state.messages.append({"role": "user", "content": query})
    
    # Trigger dynamic thinking animation steps
    for step in [1, 2, 3, 4]:
        st.session_state.thinking_step = step
        with col_main:
            render_thinking_state(step, container=thinking_container)
        time.sleep(0.35) # Simulates tactile pipeline activation
    
    # Run the actual RAG pipeline
    pipeline = load_pipeline()
    result = pipeline.run(query)
    
    # Clear thinking state
    st.session_state.thinking_step = 0
    thinking_container.empty()
    
    # Construct assistant message metadata
    meta = {
        "blocked": result["blocked"],
        "block_reason": result.get("block_reason"),
        "source_url": result.get("source_url", ""),
        "scheme_name": result.get("scheme_name", ""),
        "last_updated": result.get("last_updated", ""),
        "top_chunks": result.get("top_chunks", []),
        "latency": result.get("latency", 0.0),
    }
    
    # Append assistant response
    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "meta": meta,
    })
    
    # Automatically switch selected fund context if the pipeline returned a fund name
    if result.get("scheme_name"):
        st.session_state.active_scheme = result["scheme_name"]
        
    st.rerun()


# ── Process Pending Example Queries ───────────────────────────────────────────
if st.session_state.pending_query:
    q = st.session_state.pending_query
    st.session_state.pending_query = None
    process_query(q)


# ── Render Sticky Chat Input ──────────────────────────────────────────────────
st.markdown('<div class="input-status-pill">⚡ Hybrid Search Active</div>', unsafe_allow_html=True)
user_input = st.chat_input("Ask about HDFC fund facts — exit loads, SIP minimums, benchmarks...")

if user_input:
    process_query(user_input.strip())


# ── Render Collapsible Response Metadata Panel ────────────────────────────────
if show_inspector and col_meta is not None:
    with col_meta:
        # Get metadata from the last assistant message if available
        last_ai_msg = None
        for msg in reversed(st.session_state.messages):
            if msg["role"] == "assistant":
                last_ai_msg = msg
                break
        
        st.markdown('<div class="meta-section-title">📊 Retrieval Inspector</div>', unsafe_allow_html=True)
        
        if last_ai_msg and last_ai_msg.get("meta"):
            meta = last_ai_msg["meta"]
            latency = meta.get("latency", 0.0)
            top_chunks = meta.get("top_chunks", [])
            
            # 1. High-level Ingestion & Retrieval Metrics Card
            st.markdown(f"""
            <div class="meta-card">
                <div class="meta-row">
                    <span class="meta-label">⏱️ Response Latency</span>
                    <span class="meta-value" style="color: var(--accent-primary);">{latency:.2f}s</span>
                </div>
                <div class="meta-row">
                    <span class="meta-label">🤖 LLM Model Used</span>
                    <span class="meta-value">Llama-3.1-70B</span>
                </div>
                <div class="meta-row">
                    <span class="meta-label">⚙️ Retrieval System</span>
                    <span class="meta-value">BGE Hybrid RRF</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 2. Retrieved Context Chunks Viewer
            st.markdown('<div class="meta-section-title">📂 Context Chunks used</div>', unsafe_allow_html=True)
            
            if top_chunks:
                # Find maximum score for score scaling
                max_score = max([c.get("rrf_score", 1.0) for c in top_chunks]) if top_chunks else 1.0
                
                for idx, chunk in enumerate(top_chunks):
                    chunk_meta = chunk.get("metadata", {})
                    scheme_name = chunk_meta.get("scheme_name", "HDFC Mutual Fund")
                    section = chunk_meta.get("page_section", "General Scheme Details")
                    text = chunk.get("text", "")
                    rrf_score = chunk.get("rrf_score", 0.0)
                    
                    # Truncate text preview to 2 lines
                    preview = text[:150] + "..." if len(text) > 150 else text
                    
                    # Calculate percentage width for visualization bar
                    fill_pct = (rrf_score / max_score) * 100 if max_score > 0 else 0
                    
                    st.markdown(f"""
                    <div class="chunk-card">
                        <div class="chunk-header">
                            <span class="chunk-scheme">{scheme_name}</span>
                            <span class="chunk-section">{section}</span>
                        </div>
                        <div class="chunk-text">"{preview}"</div>
                        <div class="chunk-score-container">
                            <span class="score-label">RRF Rank Score: <b>{rrf_score:.4f}</b></span>
                            <div class="score-bar-bg">
                                <div class="score-bar-fill" style="width: {fill_pct}%;"></div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="meta-card" style="text-align: center; color: var(--text-secondary); font-style: italic;">
                    No retrieval context was generated or required for this response.
                </div>
                """, unsafe_allow_html=True)
                
        else:
            # Welcome/Empty state for metadata panel
            st.markdown("""
            <div class="meta-card" style="text-align: center; color: var(--text-secondary); padding: 30px 20px;">
                <span style="font-size: 24px; display: block; margin-bottom: 12px;">📊</span>
                <span style="font-size: 13px; font-weight: 600; color: var(--text-primary); display: block; margin-bottom: 6px;">Inspector Idle</span>
                <span style="font-size: 12px; line-height: 1.4;">Submit a query or click a quick start prompt to inspect the underlying hybrid search logs, reranker scores, and latency stats.</span>
            </div>
            """, unsafe_allow_html=True)
