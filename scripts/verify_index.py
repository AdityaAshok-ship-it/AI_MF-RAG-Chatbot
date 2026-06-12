import sys
import logging
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.retrieval.hybrid_search import HDFCHybridSearch

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("VerifyIndex")

# Golden test cases: (query, expected_scheme_substring, expected_text_keyword)
GOLDEN_TESTS = [
    ("HDFC Mid Cap exit load", "Mid Cap", "exit load"),
    ("HDFC Small Cap minimum SIP amount", "Small Cap", "sip"),
    ("HDFC Gold ETF benchmark index", "Gold", "benchmark"),
    ("HDFC Multi Cap expense ratio", "Multi Cap", "expense"),
    ("HDFC Large Cap fund manager", "Large Cap", "fund management"),
]


def run_verification():
    logger.info("Starting index verification...")
    engine = HDFCHybridSearch()

    passed = 0
    failed = 0

    for query, expected_scheme, expected_keyword in GOLDEN_TESTS:
        results = engine.search(query, limit=3)

        if not results:
            logger.error(f"FAIL: No results returned for query: '{query}'")
            failed += 1
            continue

        top = results[0]
        scheme_ok = expected_scheme.lower() in top["metadata"].get("scheme_name", "").lower()
        keyword_ok = expected_keyword.lower() in top["text"].lower()

        if scheme_ok and keyword_ok:
            logger.info(f"PASS: '{query}'")
            passed += 1
        else:
            logger.error(
                f"FAIL: '{query}' | scheme_match={scheme_ok} | keyword_match={keyword_ok} | "
                f"got scheme='{top['metadata'].get('scheme_name', '')}'"
            )
            failed += 1

    logger.info(f"Verification complete: {passed}/{passed + failed} tests passed.")

    if failed > 0:
        logger.error(f"{failed} verification test(s) FAILED. Exiting with error.")
        sys.exit(1)

    logger.info("All index verification checks passed.")


if __name__ == "__main__":
    run_verification()
