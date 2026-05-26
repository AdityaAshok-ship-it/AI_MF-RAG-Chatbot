import argparse
import sys
import logging
from pathlib import Path

# Add root folder to python path so we can resolve src packages
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.ingest.collector import GrowwCollector
from src.ingest.parser import GrowwParser
from src.ingest.chunker import MetadataChunker
from src.database.vector_store import HDFCVectorStore
from src.database.bm25_store import HDFCBM25Store

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("IngestRunner")

def run_pipeline(force_update: bool = False):
    logger.info("=========================================")
    logger.info("STARTING PHASE 0 & 1: INGESTION & RETRIEVAL SYSTEM SETUP")
    logger.info("=========================================")
    
    # ----------------------------------------------------
    # PHASE 0: Ingestion & Extraction
    # ----------------------------------------------------
    logger.info("[PHASE 0 - Step 1/3] Running Collector...")
    collector = GrowwCollector()
    collector.collect_all(force_update=force_update)
    
    logger.info("[PHASE 0 - Step 2/3] Running Parser...")
    parser = GrowwParser()
    parser.parse_all()
    
    logger.info("[PHASE 0 - Step 3/3] Running Chunker...")
    chunker = MetadataChunker()
    chunks = chunker.chunk_all()
    
    logger.info("Phase 0 complete. Chunks are fully generated.")
    
    # ----------------------------------------------------
    # PHASE 1: Indexing & Retrieval
    # ----------------------------------------------------
    logger.info("=========================================")
    logger.info("STARTING PHASE 1: INDEXING & VECTOR STORE INITIALIZATION")
    logger.info("=========================================")
    
    # Step 1: ChromaDB Dense Vector Store Ingestion
    logger.info("[PHASE 1 - Step 1/2] Indexing dense vectors...")
    vector_store = HDFCVectorStore()
    vector_store.add_chunks(chunks, force_update=force_update)
    
    # Step 2: Lexical BM25 index generation & Pickling
    logger.info("[PHASE 1 - Step 2/2] Generating sparse BM25 index...")
    bm25_store = HDFCBM25Store()
    bm25_store.build_index(chunks)
    
    logger.info("=========================================")
    logger.info("PHASE 0 & 1 PROCESS COMPLETED SUCCESSFULLY!")
    logger.info(f"Total Chunks Generated & Indexed: {len(chunks)}")
    logger.info("=========================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MFRagChatBot Ingestion & Indexing Pipeline")
    parser.add_argument("--force", action="store_true", help="Force scrape and rebuild all databases")
    args = parser.parse_args()
    
    run_pipeline(force_update=args.force)
