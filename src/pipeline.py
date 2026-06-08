import logging
import time
from src.retrieval.hybrid_search import HDFCHybridSearch
from src.retrieval.reranker import BGEReranker
from src.generation.groq_client import GroqClient
from src.generation.prompt_templates import (
    SYSTEM_PROMPT,
    build_user_prompt,
    validate_response_citation,
)
from src.guardrails.pii_filter import PIIFilter
from src.guardrails.advisory_blocker import AdvisoryBlocker

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("RAGPipeline")

_NO_CONTEXT_RESPONSE = (
    "I cannot find any official records for that query in the source documents. "
    "Please try rephrasing or ask about a specific HDFC fund detail such as exit load, "
    "expense ratio, or minimum SIP amount."
)


class RAGPipeline:
    def __init__(self):
        logger.info("Initializing RAG Pipeline...")
        self.pii_filter = PIIFilter()
        self.advisory_blocker = AdvisoryBlocker()
        self.hybrid_search = HDFCHybridSearch()
        self.reranker = BGEReranker()
        self.groq_client = GroqClient()
        logger.info("RAG Pipeline ready.")

    def run(self, user_query: str) -> dict:
        """
        Execute the full RAG pipeline for a user query.

        Returns a dict with keys:
            answer        – the final response string
            source_url    – citation URL (from top retrieved chunk)
            scheme_name   – scheme the answer is about
            last_updated  – data freshness date
            blocked       – True if the query was refused (PII / advisory)
            block_reason  – "pii" | "advisory" | None
            top_chunks    – list of retrieved chunks used
            latency       – response generation latency in seconds
        """
        logger.info(f"Pipeline received query: '{user_query}'")
        start_time = time.time()

        # Step 1: PII guard — check before touching any retrieval or LLM
        if self.pii_filter.contains_pii(user_query):
            latency = time.time() - start_time
            return {
                "answer": self.pii_filter.get_refusal_message(),
                "source_url": "",
                "scheme_name": "",
                "last_updated": "",
                "blocked": True,
                "block_reason": "pii",
                "top_chunks": [],
                "latency": latency,
            }

        # Step 2: Advisory intent guard
        if self.advisory_blocker.is_advisory(user_query):
            latency = time.time() - start_time
            return {
                "answer": self.advisory_blocker.get_refusal_message(),
                "source_url": "",
                "scheme_name": "",
                "last_updated": "",
                "blocked": True,
                "block_reason": "advisory",
                "top_chunks": [],
                "latency": latency,
            }

        # Step 3: Hybrid retrieval (dense + sparse → RRF, top 10 candidates)
        candidates = self.hybrid_search.search(user_query, limit=10)

        if not candidates:
            latency = time.time() - start_time
            return {
                "answer": _NO_CONTEXT_RESPONSE,
                "source_url": "",
                "scheme_name": "",
                "last_updated": "",
                "blocked": False,
                "block_reason": None,
                "top_chunks": [],
                "latency": latency,
            }

        # Step 4: Rerank candidates → top 3 high-relevance chunks
        top_chunks = self.reranker.rerank(user_query, candidates, top_k=3)

        # Step 5: Build RAG prompt and call Groq
        user_prompt = build_user_prompt(user_query, top_chunks)

        try:
            result = self.groq_client.generate(SYSTEM_PROMPT, user_prompt)
            raw_response = result["response"]
        except RuntimeError as e:
            # Groq retry exhausted — return friendly error
            latency = time.time() - start_time
            return {
                "answer": str(e),
                "source_url": "",
                "scheme_name": "",
                "last_updated": "",
                "blocked": False,
                "block_reason": None,
                "top_chunks": top_chunks,
                "latency": latency,
            }

        # Step 6: Citation validation — ensure response has a valid Groww URL
        validated_response = validate_response_citation(raw_response, top_chunks)

        # Extract citation metadata from top chunk for structured return
        top_meta = top_chunks[0].get("metadata", {}) if top_chunks else {}

        latency = time.time() - start_time
        return {
            "answer": validated_response,
            "source_url": top_meta.get("source_url", ""),
            "scheme_name": top_meta.get("scheme_name", ""),
            "last_updated": top_meta.get("last_updated_date", ""),
            "blocked": False,
            "block_reason": None,
            "top_chunks": top_chunks,
            "latency": latency,
        }
