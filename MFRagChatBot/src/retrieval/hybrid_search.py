import logging
from src.database.vector_store import HDFCVectorStore
from src.database.bm25_store import HDFCBM25Store

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("HybridSearch")

class HDFCHybridSearch:
    def __init__(self):
        self.vector_store = HDFCVectorStore()
        self.bm25_store = HDFCBM25Store()
        
        # Load BM25 index once
        self.index_loaded = self.bm25_store.load_index()
        if not self.index_loaded:
            logger.warning("BM25 index not pre-loaded. Ensure Phase 1 ingestion is executed.")

    def search(self, query: str, limit: int = 5, rrf_k: int = 60) -> list:
        """Perform dense and sparse search, and merge using Reciprocal Rank Fusion (RRF)."""
        logger.info(f"Initiating hybrid search for query: '{query}'")
        
        # Retrieve candidate chunks (fetch 15 from each to have a healthy candidate pool)
        dense_results = self.vector_store.search(query, limit=15)
        
        # Refresh index if not loaded
        if not self.index_loaded:
            self.index_loaded = self.bm25_store.load_index()
            
        sparse_results = self.bm25_store.search(query, limit=15)
        
        # RRF logic: RRF_Score(doc) = 1/(k + rank_dense) + 1/(k + rank_sparse)
        rrf_scores = {}
        chunk_lookup = {} # Maps chunk_id to chunk dictionary to keep metadata intact

        # 1. Process Dense Results
        for rank, chunk in enumerate(dense_results, start=1):
            chunk_id = chunk["chunk_id"]
            chunk_lookup[chunk_id] = {
                "chunk_id": chunk_id,
                "text": chunk["text"],
                "metadata": chunk["metadata"]
            }
            
            # Reciprocal rank scoring
            if chunk_id not in rrf_scores:
                rrf_scores[chunk_id] = {"dense_rank": rank, "sparse_rank": 999} # Default sparse rank 999
            else:
                rrf_scores[chunk_id]["dense_rank"] = rank

        # 2. Process Sparse Results
        for rank, chunk in enumerate(sparse_results, start=1):
            chunk_id = chunk["chunk_id"]
            chunk_lookup[chunk_id] = {
                "chunk_id": chunk_id,
                "text": chunk["text"],
                "metadata": chunk["metadata"]
            }
            
            # Reciprocal rank scoring
            if chunk_id not in rrf_scores:
                rrf_scores[chunk_id] = {"dense_rank": 999, "sparse_rank": rank} # Default dense rank 999
            else:
                rrf_scores[chunk_id]["sparse_rank"] = rank

        # 3. Calculate final RRF Scores
        final_scores = []
        for chunk_id, ranks in rrf_scores.items():
            # RRF Math
            dense_score = 1.0 / (rrf_k + ranks["dense_rank"])
            sparse_score = 1.0 / (rrf_k + ranks["sparse_rank"])
            total_rrf_score = dense_score + sparse_score
            
            # Store final score alongside chunk info
            chunk_info = chunk_lookup[chunk_id]
            chunk_info["rrf_score"] = total_rrf_score
            final_scores.append(chunk_info)

        # Sort combined results by RRF score descending
        final_scores.sort(key=lambda x: x["rrf_score"], reverse=True)
        
        logger.info(f"Hybrid search returned {len(final_scores)} merged candidate chunks. Truncating to top {limit}.")
        return final_scores[:limit]

if __name__ == "__main__":
    engine = HDFCHybridSearch()
    res = engine.search("HDFC exit load Opportunities Fund")
    for r in res:
        print(f"[{r['rrf_score']:.6f}] {r['chunk_id']} -> {r['text'][:100]}")
