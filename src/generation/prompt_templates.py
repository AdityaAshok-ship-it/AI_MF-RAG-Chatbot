import logging

logger = logging.getLogger("PromptTemplates")

ALLOWED_GROWW_DOMAINS = ["groww.in/mutual-funds/"]

SYSTEM_PROMPT = """You are a strict facts-only Mutual Fund information assistant for HDFC schemes listed on Groww.

RULES — follow every rule with zero exceptions:
1. Answer ONLY using information in the CONTEXT provided. Never use your pre-trained knowledge.
2. Your answer MUST be 3 sentences or fewer.
3. Include EXACTLY ONE citation link. The link must be copied verbatim from the `source_url` field in the CONTEXT. Do NOT invent URLs.
4. End your response with a footer on its own line: "Last updated from sources: <last_updated_date>" using the date from the CONTEXT.
5. If the answer is not found in the CONTEXT, respond exactly: "I cannot find any official records for that query in the source documents."
6. Never evaluate investment quality, make comparisons, or recommend funds. Refuse any such query.
7. Never reveal or process personal identification information (PAN, Aadhaar, phone numbers, emails).

RESPONSE FORMAT:
<your factual answer in ≤3 sentences>

Source: <groww_url_from_context>
Last updated from sources: <date_from_context>"""


def build_user_prompt(query: str, context_chunks: list) -> str:
    """Format retrieved chunks and the user query into a RAG prompt payload."""
    context_parts = []
    for i, chunk in enumerate(context_chunks, start=1):
        meta = chunk.get("metadata", {})
        source_url = meta.get("source_url", "")
        scheme_name = meta.get("scheme_name", "Unknown Scheme")
        page_section = meta.get("page_section", "General")
        last_updated = meta.get("last_updated_date", "N/A")
        text = chunk.get("text", "")

        context_parts.append(
            f"[CONTEXT {i}]\n"
            f"Scheme: {scheme_name}\n"
            f"Section: {page_section}\n"
            f"source_url: {source_url}\n"
            f"last_updated_date: {last_updated}\n"
            f"---\n{text}"
        )

    context_block = "\n\n".join(context_parts)
    return f"CONTEXT:\n{context_block}\n\nQUESTION: {query}"


def validate_response_citation(response_text: str, context_chunks: list) -> str:
    """
    Ensure the LLM response contains a valid Groww URL from the retrieved chunks.
    If no valid URL is found, inject the source_url from the top-ranked chunk.
    """
    allowed_urls = [
        chunk.get("metadata", {}).get("source_url", "")
        for chunk in context_chunks
        if chunk.get("metadata", {}).get("source_url", "")
    ]

    for url in allowed_urls:
        if url and url in response_text:
            return response_text  # Citation is valid

    # Citation missing or hallucinated — inject the top chunk's source_url
    if allowed_urls:
        top_url = allowed_urls[0]
        top_date = context_chunks[0].get("metadata", {}).get("last_updated_date", "N/A")
        logger.warning("Response missing valid citation. Injecting top chunk source_url.")

        # Strip any hallucinated Source: line and append correct one
        lines = [ln for ln in response_text.splitlines() if not ln.strip().startswith("Source:") and not ln.strip().startswith("Last updated")]
        cleaned = "\n".join(lines).strip()
        return f"{cleaned}\n\nSource: {top_url}\nLast updated from sources: {top_date}"

    return response_text
