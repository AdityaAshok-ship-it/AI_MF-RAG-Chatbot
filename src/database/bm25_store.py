import json
import logging
import pickle
import re
from pathlib import Path
from src import config

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("BM25Store")

# Flag for indicating fallback mode
BM25_FALLBACK = False

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    logger.warning("rank_bm25 package is missing! Enabling lightweight local lexical indexer fallback.")
    BM25_FALLBACK = True

class HDFCBM25Store:
    def __init__(self):
        self.index_path = Path(config.PROCESSED_DATA_DIR) / "bm25_index.pkl"
        self.bm25 = None
        self.corpus = [] # Holds original chunk records

    def tokenize(self, text: str) -> list:
        """Tokenize and clean text: lowercase, remove non-alphanumeric, split."""
        text = text.lower()
        # Remove punctuation, keep numbers and letters
        words = re.findall(r'[a-z0-9%]+', text)
        return words

    def build_index(self, chunks: list):
        """Build and persist BM25 index on text chunks."""
        global BM25_FALLBACK
        if not chunks:
            logger.warning("No chunks provided to build BM25 index.")
            return

        self.corpus = chunks
        tokenized_corpus = [self.tokenize(c["text"]) for c in chunks]

        if not BM25_FALLBACK:
            try:
                self.bm25 = BM25Okapi(tokenized_corpus)
                logger.info("BM25Okapi index built successfully.")
            except Exception as e:
                logger.error(f"Error building BM25 index: {e}. Enabling fallback.")
                BM25_FALLBACK = True

        if BM25_FALLBACK:
            # Fallback simple TF-IDF or frequency store
            logger.info("Local Fallback: Initializing local word-frequency lexical indexing...")
            self.bm25 = None

        # Persist index data
        self.save_index()

    def save_index(self):
        """Pickle the built index structures to disk."""
        try:
            with open(self.index_path, "wb") as f:
                pickle.dump({
                    "corpus": self.corpus,
                    "bm25_fallback": BM25_FALLBACK,
                    # We can pick rank_bm25 objects if BM25Okapi supports it, which it does
                    "bm25_object": self.bm25 if not BM25_FALLBACK else None
                }, f)
            logger.info("BM25 index successfully saved to disk.")
        except Exception as e:
            logger.error(f"Failed to save BM25 index to pickle: {e}")

    def load_index(self) -> bool:
        """Load pickled index structure from disk. Returns True if successful."""
        global BM25_FALLBACK
        if not self.index_path.exists():
            logger.warning(f"No existing BM25 index file found at: {self.index_path}")
            return False

        try:
            with open(self.index_path, "rb") as f:
                data = pickle.load(f)
                self.corpus = data["corpus"]

                BM25_FALLBACK = data["bm25_fallback"]
                
                if not BM25_FALLBACK:
                    self.bm25 = data["bm25_object"]
                else:
                    self.bm25 = None
            logger.info(f"Successfully loaded BM25 index with {len(self.corpus)} chunks.")
            return True
        except Exception as e:
            logger.error(f"Failed to load BM25 index: {e}")
            return False

    def search(self, query: str, limit: int = 10) -> list:
        """Query sparse keyword matching score and return top-k matches."""
        if not self.corpus:
            logger.warning("BM25 corpus is empty. Cannot search.")
            return []

        tokenized_query = self.tokenize(query)

        if not BM25_FALLBACK and self.bm25:
            try:
                # Retrieve BM25 scores
                scores = self.bm25.get_scores(tokenized_query)
                
                # Pair and sort chunks by score descending
                scored_chunks = list(zip(scores, self.corpus))
                scored_chunks.sort(key=lambda x: x[0], reverse=True)
                
                results = []
                for score, chunk in scored_chunks[:limit]:
                    if score <= 0:
                        continue # Skip zero matches
                    results.append({
                        "chunk_id": chunk["chunk_id"],
                        "text": chunk["text"],
                        "metadata": chunk["metadata"],
                        "score": score
                    })
                return results
            except Exception as e:
                logger.error(f"BM25 search failed: {e}. Proceeding with fallback.")

        # Fallback keyword overlap score
        logger.info("Using local fallback lexical query resolver...")
        query_set = set(tokenized_query)
        scored_chunks = []
        
        for chunk in self.corpus:
            chunk_tokens = self.tokenize(chunk["text"])
            chunk_set = set(chunk_tokens)
            # score is count of unique overlaps
            overlap_score = len(query_set.intersection(chunk_set))
            if overlap_score > 0:
                scored_chunks.append((overlap_score, chunk))
                
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        
        results = []
        for score, chunk in scored_chunks[:limit]:
            results.append({
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "metadata": chunk["metadata"],
                "score": float(score)
            })
        return results

if __name__ == "__main__":
    store = HDFCBM25Store()
    if store.load_index():
        res = store.search("HDFC exit load")
        print(f"BM25 test matched: {len(res)} results.")
