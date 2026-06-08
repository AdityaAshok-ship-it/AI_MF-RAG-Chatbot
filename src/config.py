import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base Workspace Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Data Directories
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
VECTOR_DB_DIR = DATA_DIR / "vector_db"

# Create directories if they do not exist
for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, VECTOR_DB_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Groww Mutual Fund Target URLs
TARGET_URLS = [
    "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth",
    "https://groww.in/mutual-funds/hdfc-multi-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth"
]

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
HF_TOKEN = os.getenv("HF_TOKEN", "")

# Embedding Configuration
EMBEDDING_MODEL_NAME = "BAAI/bge-large-en-v1.5"
RERANK_MODEL_NAME = "BAAI/bge-reranker-large"

# Chunker Configuration
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150

# Ingestion Metadata
DOCUMENT_HASHES_PATH = DATA_DIR / "document_hashes.json"
