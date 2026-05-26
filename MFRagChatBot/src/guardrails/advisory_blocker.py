import re
import logging

logger = logging.getLogger("AdvisoryBlocker")

AMFI_EDUCATION_URL = "https://www.amfiindia.com/investor-corner"

# Keyword-based advisory intent triggers (fast path)
_ADVISORY_KEYWORDS = [
    r'\bshould i\b', r'\bshould we\b',
    r'\bbuy\b', r'\bsell\b', r'\binvest\b', r'\binvestment advice\b',
    r'\brecommend\b', r'\brecommendation\b',
    r'\bbetter than\b', r'\bvs\b', r'\bversus\b', r'\bcompare\b', r'\bcomparison\b',
    r'\bpredict\b', r'\bforecast\b', r'\bfuture return\b', r'\bexpected return\b',
    r'\bdouble my money\b', r'\bget rich\b', r'\bprofit\b',
    r'\bwhich fund\b', r'\bbest fund\b', r'\btop fund\b',
    r'\bworth it\b', r'\bgood investment\b', r'\bsafe investment\b',
    r'\bwill it grow\b', r'\bwill it rise\b', r'\bwill the nav\b',
]

_ADVISORY_PATTERNS = [re.compile(kw, re.IGNORECASE) for kw in _ADVISORY_KEYWORDS]

_REFUSAL_TEMPLATE = (
    "I'm a facts-only assistant and cannot provide investment advice, recommendations, "
    "or performance predictions. For guidance on mutual fund investing, please visit "
    f"AMFI's Investor Education portal: {AMFI_EDUCATION_URL}"
)

# Known advisory query vectors for semantic fallback (stored as text; embedded lazily)
_ADVISORY_SEED_QUERIES = [
    "should I invest in HDFC Mid Cap fund",
    "is HDFC Small Cap better than Large Cap",
    "which HDFC fund will give the best returns",
    "predict returns for HDFC Gold ETF",
    "recommend a mutual fund for me",
    "will HDFC Multi Cap double my money",
    "buy HDFC Large Cap fund or not",
]


class AdvisoryBlocker:
    def __init__(self):
        self._embedder = None
        self._advisory_vectors = None
        self._semantic_threshold = 0.85
        # Semantic model intentionally not loaded at startup — keyword matching
        # alone covers all advisory patterns and avoids a 200MB model load.

    def _try_load_semantic(self):
        """Lazily load a lightweight embedding model for semantic intent detection."""
        try:
            from sentence_transformers import SentenceTransformer
            import numpy as np
            # Use a small/fast model to keep startup cost low
            self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
            self._advisory_vectors = self._embedder.encode(
                _ADVISORY_SEED_QUERIES, normalize_embeddings=True
            )
            logger.info("AdvisoryBlocker: semantic model loaded (all-MiniLM-L6-v2).")
        except Exception as e:
            logger.warning(f"AdvisoryBlocker: semantic model unavailable ({e}). Keyword-only mode.")
            self._embedder = None
            self._advisory_vectors = None

    def _keyword_match(self, query: str) -> bool:
        for pattern in _ADVISORY_PATTERNS:
            if pattern.search(query):
                return True
        return False

    def _semantic_match(self, query: str) -> bool:
        if self._embedder is None or self._advisory_vectors is None:
            return False
        try:
            import numpy as np
            query_vec = self._embedder.encode(query, normalize_embeddings=True)
            # Cosine similarity (vectors are already normalized)
            similarities = self._advisory_vectors @ query_vec
            max_sim = float(np.max(similarities))
            logger.debug(f"AdvisoryBlocker max semantic similarity: {max_sim:.3f}")
            return max_sim >= self._semantic_threshold
        except Exception as e:
            logger.warning(f"Semantic similarity check failed: {e}")
            return False

    def is_advisory(self, query: str) -> bool:
        """Return True if the query is classified as financial advice / speculative."""
        if self._keyword_match(query):
            logger.info("AdvisoryBlocker: keyword match — query flagged as advisory.")
            return True
        if self._semantic_match(query):
            logger.info("AdvisoryBlocker: semantic match — query flagged as advisory.")
            return True
        return False

    def get_refusal_message(self) -> str:
        return _REFUSAL_TEMPLATE
