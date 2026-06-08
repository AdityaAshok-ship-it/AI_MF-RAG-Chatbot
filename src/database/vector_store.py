import json
import logging
import os
from pathlib import Path
from src import config

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("VectorStore")

# Flag for indicating fallback mode
FALLBACK_MODE = False

try:
    import chromadb
    from sentence_transformers import SentenceTransformer
except ImportError:
    logger.warning("ChromaDB or SentenceTransformers missing! Enabling lightweight local vector search fallback.")
    FALLBACK_MODE = True

class HDFCVectorStore:
    def __init__(self):
        global FALLBACK_MODE
        self.db_dir = Path(config.VECTOR_DB_DIR)
        self.model_name = config.EMBEDDING_MODEL_NAME
        self.db_dir.mkdir(parents=True, exist_ok=True)

        if not FALLBACK_MODE:
            try:
                # Initialize persistent Chroma client
                self.client = chromadb.PersistentClient(path=str(self.db_dir))

                # Load BGE embedding model on CPU/GPU safely
                logger.info(f"Loading embedding model: {self.model_name}...")
                self.embedder = SentenceTransformer(self.model_name)

                # Get or create collection
                self.collection = self.client.get_or_create_collection(
                    name="hdfc_mutual_funds",
                    metadata={"hnsw:space": "cosine"} # Use cosine similarity
                )
                logger.info("ChromaDB Vector Store initialized successfully.")
            except Exception as e:
                logger.error(f"Error initializing ChromaDB: {e}. Switching to fallback mode.")
                FALLBACK_MODE = True
                
        if FALLBACK_MODE:
            self.collection = None
            self.embedder = None
            self.fallback_db_path = self.db_dir / "fallback_db.json"
            self.fallback_data = self.load_fallback_data()

    def load_fallback_data(self) -> list:
        """Load fallback records if Chroma is not available."""
        if self.fallback_db_path.exists():
            try:
                with open(self.fallback_db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading fallback database: {e}")
        return []

    def save_fallback_data(self):
        """Save fallback records to file."""
        try:
            with open(self.fallback_db_path, "w", encoding="utf-8") as f:
                json.dump(self.fallback_data, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving fallback database: {e}")

    def add_chunks(self, chunks: list, force_update: bool = False):
        """Generate BGE embeddings in batch and upsert chunks to database."""
        if not chunks:
            logger.warning("No chunks provided to index.")
            return

        if FALLBACK_MODE:
            logger.info("Fallback Ingestion: Storing raw text and metadata chunks locally...")
            existing_ids = {c["chunk_id"] for c in self.fallback_data}
            updated = 0
            for chunk in chunks:
                if force_update or chunk["chunk_id"] not in existing_ids:
                    # Remove existing if force update
                    self.fallback_data = [c for c in self.fallback_data if c["chunk_id"] != chunk["chunk_id"]]
                    self.fallback_data.append(chunk)
                    updated += 1
            self.save_fallback_data()
            logger.info(f"Fallback Ingestion complete. Added/Updated {updated} records.")
            return

        logger.info(f"Ingesting {len(chunks)} chunks into ChromaDB...")
        ids = []
        texts = []
        metadatas = []
        
        for chunk in chunks:
            ids.append(chunk["chunk_id"])
            texts.append(chunk["text"])
            
            # ChromaDB only accepts string/int/float/bool metadata values
            meta = {
                "source_url": chunk["metadata"]["source_url"],
                "scheme_name": chunk["metadata"]["scheme_name"],
                "document_type": chunk["metadata"]["document_type"],
                "page_section": chunk["metadata"]["page_section"],
                "last_updated_date": chunk["metadata"]["last_updated_date"]
            }
            metadatas.append(meta)

        try:
            # Mitigation Edge Case 1.1: OOM Prevention
            # Enforce batch-size during BGE embedding generation
            logger.info("Computing dense BGE embeddings in batches...")
            embeddings = self.embedder.encode(
                texts, 
                batch_size=16, # Mitigate memory usage on low-spec CPUs/runners
                show_progress_bar=True,
                normalize_embeddings=True
            ).tolist()

            logger.info("Upserting vectors into ChromaDB HNSW Index...")
            # Upsert into ChromaDB
            self.collection.upsert(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )
            logger.info("Database ingestion complete. Index fully updated.")
        except Exception as e:
            logger.error(f"Failed to upsert chunks into ChromaDB: {e}")
            raise

    def search(self, query: str, limit: int = 10) -> list:
        """Search dense database using BGE embedding similarity."""
        if FALLBACK_MODE:
            # Fallback search logic: metadata matching & simple lexical scanning
            logger.info(f"Fallback Search: Scanning {len(self.fallback_data)} local records...")
            scored_results = []
            query_words = set(query.lower().split())
            
            for chunk in self.fallback_data:
                # Basic overlap score
                chunk_words = set(chunk["text"].lower().split())
                score = len(query_words.intersection(chunk_words)) / max(1, len(query_words))
                scored_results.append((score, chunk))
                
            # Sort by score descending
            scored_results.sort(key=lambda x: x[0], reverse=True)
            
            results = []
            for score, chunk in scored_results[:limit]:
                results.append({
                    "chunk_id": chunk["chunk_id"],
                    "text": chunk["text"],
                    "metadata": chunk["metadata"],
                    "distance": 1.0 - score # Cosine-distance analogue
                })
            return results

        try:
            # Generate query embedding
            query_vector = self.embedder.encode(query, normalize_embeddings=True).tolist()
            
            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=limit
            )
            
            formatted = []
            if results and results["ids"]:
                for i in range(len(results["ids"][0])):
                    formatted.append({
                        "chunk_id": results["ids"][0][i],
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if results["distances"] else 0.5
                    })
            return formatted
        except Exception as e:
            logger.error(f"Search query failed in ChromaDB: {e}")
            return []

if __name__ == "__main__":
    store = HDFCVectorStore()
    # Test empty search
    res = store.search("HDFC Mid Cap exit load")
    print(f"Test retrieved: {len(res)} results.")
