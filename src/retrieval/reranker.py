import logging

logger = logging.getLogger("BGEReranker")

# Minimum number of candidates needed to justify running the cross-encoder.
# With ≤ this many chunks, RRF ordering is already optimal — skip the heavy model.
_RERANK_MIN_CANDIDATES = 10


class BGEReranker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-large"):
        self.model_name = model_name
        self.model = None
        # Model is loaded lazily on first rerank call with enough candidates.

    def _load_model(self):
        try:
            from sentence_transformers import CrossEncoder
            logger.info(f"Loading reranker model: {self.model_name}...")
            self.model = CrossEncoder(self.model_name)
            logger.info("BGE Reranker loaded successfully.")
        except Exception as e:
            logger.warning(f"Failed to load reranker model: {e}. Passthrough mode active.")
            self.model = None

    def rerank(self, query: str, chunks: list, top_k: int = 3) -> list:
        """
        Score (query, chunk_text) pairs with the cross-encoder and return top_k chunks.
        Skipped entirely when fewer than _RERANK_MIN_CANDIDATES chunks are available,
        since RRF ordering is already reliable for small corpora.
        """
        if not chunks:
            return []

        # Skip reranker for small corpora — avoids loading a 300MB model for no gain
        if len(chunks) < _RERANK_MIN_CANDIDATES:
            logger.info(f"Reranker skipped ({len(chunks)} chunks < {_RERANK_MIN_CANDIDATES} threshold). Using RRF order.")
            return chunks[:top_k]

        # Lazy-load model only when corpus is large enough to benefit
        if self.model is None:
            self._load_model()

        if self.model is None:
            return chunks[:top_k]

        try:
            pairs = [(query, chunk["text"]) for chunk in chunks]
            scores = self.model.predict(pairs)
            scored = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)
            top_chunks = [chunk for _, chunk in scored[:top_k]]
            logger.info(f"Reranker selected top {len(top_chunks)} from {len(chunks)} candidates.")
            return top_chunks
        except Exception as e:
            logger.error(f"Reranker scoring failed: {e}. Returning RRF order.")
            return chunks[:top_k]
