import sys
import logging
from pathlib import Path

# Add root folder to python path so we can resolve src packages
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.retrieval.hybrid_search import HDFCHybridSearch

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("RetrievalTest")

def run_retrieval_tests():
    logger.info("=========================================")
    logger.info("RUNNING RETRIEVAL RECALL UNIT TESTS (PHASE 1)")
    logger.info("=========================================")
    
    try:
        search_engine = HDFCHybridSearch()
    except Exception as e:
        logger.error(f"Failed to load search engine: {e}")
        logger.error("Make sure to run 'python scripts/ingest.py' before executing retrieval tests.")
        return False

    # 10 golden test cases as required by eval.md (Phase 1 criterion)
    tests = [
        {
            "query": "What is the exit load for HDFC Mid Cap Opportunities Fund?",
            "keywords": ["exit", "load"],
            "scheme": "Mid Cap"
        },
        {
            "query": "HDFC Small Cap minimum investment SIP amount",
            "keywords": ["sip", "minimum"],
            "scheme": "Small Cap"
        },
        {
            "query": "Benchmark index followed by HDFC Large Cap Fund",
            "keywords": ["benchmark", "nifty"],
            "scheme": "Large Cap"
        },
        {
            "query": "What is the expense ratio of HDFC Multi Cap Fund?",
            "keywords": ["expense", "ratio"],
            "scheme": "Multi Cap"
        },
        {
            "query": "HDFC Gold ETF Fund of Fund exit load details",
            "keywords": ["exit", "gold"],
            "scheme": "Gold"
        },
        {
            "query": "Who are the fund managers of HDFC Small Cap Fund?",
            "keywords": ["fund", "manager"],
            "scheme": "Small Cap"
        },
        {
            "query": "What is the minimum lump sum investment for HDFC Mid Cap?",
            "keywords": ["lumpsum", "minimum"],
            "scheme": "Mid Cap"
        },
        {
            "query": "HDFC Large Cap Fund riskometer risk level",
            "keywords": ["risk", "large"],
            "scheme": "Large Cap"
        },
        {
            "query": "Top holdings of HDFC Multi Cap Fund portfolio",
            "keywords": ["holding", "portfolio"],
            "scheme": "Multi Cap"
        },
        {
            "query": "AUM of HDFC Small Cap Fund assets under management",
            "keywords": ["aum", "assets"],
            "scheme": "Small Cap"
        },
    ]

    passed = 0
    total = len(tests)

    for i, t in enumerate(tests, 1):
        logger.info(f"Test case {i}/{total}: '{t['query']}'")
        results = search_engine.search(t["query"], limit=3)
        
        if not results:
            logger.error(f"  FAILED: No chunks returned for query!")
            continue
            
        top_match = results[0]
        text_lower = top_match["text"].lower()
        scheme_name = top_match["metadata"]["scheme_name"]
        
        # Verify scheme match
        scheme_ok = t["scheme"].lower() in scheme_name.lower() or t["scheme"].replace("-", " ").lower() in scheme_name.lower()
        
        # Verify key phrase match
        keyword_matches = [k for k in t["keywords"] if k.lower() in text_lower or k.lower() in scheme_name.lower()]
        keywords_ok = len(keyword_matches) >= 2 # at least 2 key terms must match
        
        if scheme_ok and keywords_ok:
            logger.info(f"  PASSED! Top match: '{scheme_name}' (Score: {top_match['rrf_score']:.6f})")
            passed += 1
        else:
            logger.error(f"  FAILED.")
            logger.error(f"    Expected Scheme: '{t['scheme']}' -> Got: '{scheme_name}'")
            logger.error(f"    Expected Keywords: {t['keywords']} -> Matched: {keyword_matches}")
            logger.error(f"    Top Match Snippet: {top_match['text'][:150]}...")

    # RRF score sanity check — no duplicates, valid range, descending order
    logger.info("Running RRF score integrity check...")
    rrf_results = search_engine.search("HDFC mutual fund exit load expense ratio benchmark", limit=10)
    rrf_ok = True
    if rrf_results:
        scores = [r["rrf_score"] for r in rrf_results]
        ids = [r["chunk_id"] for r in rrf_results]
        if scores != sorted(scores, reverse=True):
            logger.error("RRF SCORE CHECK FAILED: results not in descending order.")
            rrf_ok = False
        if len(ids) != len(set(ids)):
            logger.error("RRF SCORE CHECK FAILED: duplicate chunk_ids in results.")
            rrf_ok = False
        if any(s <= 0 for s in scores):
            logger.error("RRF SCORE CHECK FAILED: non-positive RRF scores detected.")
            rrf_ok = False
        if rrf_ok:
            logger.info(f"RRF score check PASSED. Top score: {scores[0]:.6f}, bottom: {scores[-1]:.6f}")
    else:
        logger.warning("RRF score check skipped — no results returned (index may be empty).")

    logger.info("=========================================")
    logger.info(f"RETRIEVAL RECALL SUMMARY: {passed}/{total} TESTS PASSED | RRF check: {'PASS' if rrf_ok else 'FAIL'}")
    logger.info("=========================================")
    return passed == total and rrf_ok

if __name__ == "__main__":
    run_retrieval_tests()
