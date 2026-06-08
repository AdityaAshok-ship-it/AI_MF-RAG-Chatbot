import json
import logging
from pathlib import Path
from bs4 import BeautifulSoup
from src import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class GrowwParser:
    def __init__(self):
        self.raw_dir = config.RAW_DATA_DIR
        self.processed_dir = config.PROCESSED_DATA_DIR

    def _parse_lock_in(self, raw: object) -> str:
        """Convert the lock_in dict/value to a human-readable string."""
        if not raw or raw == "No Lock-in":
            return "No lock-in period"
        if isinstance(raw, dict):
            parts = []
            if raw.get("years"):
                parts.append(f"{raw['years']} year(s)")
            if raw.get("months"):
                parts.append(f"{raw['months']} month(s)")
            if raw.get("days"):
                parts.append(f"{raw['days']} day(s)")
            return ", ".join(parts) if parts else "No lock-in period"
        return str(raw)

    def parse_file(self, file_path: Path) -> dict:
        """Parse a single raw HTML file and extract the 5 priority fields + context metadata."""
        logger.info(f"Parsing raw HTML: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, "html.parser")
        next_data_script = soup.find("script", id="__NEXT_DATA__")

        if not next_data_script:
            raise ValueError(f"No __NEXT_DATA__ script tag found in: {file_path}")

        try:
            data = json.loads(next_data_script.string)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to decode __NEXT_DATA__ JSON in {file_path}: {e}")

        sd = data.get("props", {}).get("pageProps", {}).get("mfServerSideData", {})
        if not sd:
            raise ValueError(f"'mfServerSideData' missing in {file_path}")

        # ── Identity ──────────────────────────────────────────────────────────
        scheme_name  = sd.get("scheme_name", "")
        category     = sd.get("category", "")
        sub_category = sd.get("sub_category", "")
        launch_date  = sd.get("launch_date", "")
        benchmark    = sd.get("benchmark", "")
        benchmark_name = sd.get("benchmark_name", "")
        description  = sd.get("description", "")
        riskometer   = sd.get("nfo_risk") or ("Very High" if any(
            x in str(file_path).lower() for x in ("small-cap", "mid-cap")) else "Moderately High")
        lock_in      = self._parse_lock_in(sd.get("lock_in"))

        # ── PRIORITY FIELD 1: NAV ─────────────────────────────────────────────
        nav      = sd.get("nav")          # e.g. 223.135
        nav_date = sd.get("nav_date", "") # e.g. "26-May-2026"

        # ── PRIORITY FIELD 2: Expense Ratio ───────────────────────────────────
        expense_ratio = sd.get("expense_ratio")  # e.g. "0.73" (percent)

        # ── PRIORITY FIELD 3: Fund Size (AUM) ────────────────────────────────
        aum = sd.get("aum")  # e.g. 94744.7175 (Crores)

        # ── PRIORITY FIELD 4: SIP ────────────────────────────────────────────
        min_sip      = sd.get("min_sip_investment", 100)
        min_lumpsum  = sd.get("min_investment_amount", 500)
        exit_load    = sd.get("exit_load", "NIL")

        # ── PRIORITY FIELD 5: Fund Management ────────────────────────────────
        # Primary manager is a scalar; details list uses "person_name"
        raw_mgrs = sd.get("fund_manager_details", [])
        managers = []
        for m in raw_mgrs:
            name = m.get("person_name") or m.get("manager_name") or m.get("name", "")
            exp  = m.get("experience", "")
            edu  = m.get("education", "")
            if name:
                managers.append({"name": name, "experience": exp, "education": edu})
        # Fallback: use the scalar fund_manager field if details list is empty
        if not managers and sd.get("fund_manager"):
            managers = [{"name": sd["fund_manager"], "experience": "", "education": ""}]

        # ── Holdings (top 20 by corpus_per) ──────────────────────────────────
        raw_holdings = sd.get("holdings", [])
        holdings = []
        for h in raw_holdings:
            name   = h.get("company_name") or h.get("stock_name") or h.get("name", "")
            sector = h.get("sector_name") or h.get("sector", "")
            # Groww uses "corpus_per" for the portfolio weight percentage
            pct    = h.get("corpus_per") or h.get("corpus_pct") or h.get("percentage") or 0.0
            if name:
                holdings.append({"company_name": name, "sector": sector, "percentage": round(float(pct), 2)})
        # Sort descending by weight and keep top 20
        holdings.sort(key=lambda x: x["percentage"], reverse=True)
        holdings = holdings[:20]

        return {
            "scheme_name":    scheme_name,
            "category":       category,
            "sub_category":   sub_category,
            "riskometer":     riskometer,
            "launch_date":    launch_date,
            "lock_in":        lock_in,
            "benchmark":      benchmark,
            "benchmark_name": benchmark_name,
            "description":    description,
            # Priority fields
            "nav":            nav,
            "nav_date":       nav_date,
            "expense_ratio":  expense_ratio,
            "aum":            aum,
            "min_sip":        min_sip,
            "min_lumpsum":    min_lumpsum,
            "exit_load":      exit_load,
            "managers":       managers,
            "holdings":       holdings,
        }

    def convert_to_markdown(self, info: dict, url: str) -> str:
        """Convert parsed scheme dict to a focused Markdown document for RAG ingestion."""
        md = []

        # ── Header ────────────────────────────────────────────────────────────
        md.append(f"# Scheme Profile: {info['scheme_name']}")
        md.append(f"**Source Citation URL:** {url}")
        md.append(f"**AMC:** HDFC Mutual Fund")
        md.append(f"**Category:** {info['category']} ({info['sub_category']})")
        md.append(f"**Risk Level:** {info['riskometer']}")
        md.append(f"**Launch Date:** {info['launch_date']}")
        md.append(f"**Lock-in Period:** {info['lock_in']}")
        md.append(f"**Benchmark Index:** {info['benchmark_name']} ({info['benchmark']})")
        md.append("")

        md.append("## Investment Objective")
        md.append(info["description"] or "No description available.")
        md.append("")

        # ── PRIORITY 1: NAV ───────────────────────────────────────────────────
        md.append("## Current NAV (Net Asset Value)")
        if info["nav"] is not None:
            md.append(f"*   **NAV:** ₹{info['nav']} per unit")
            md.append(f"*   **As of Date:** {info['nav_date']}")
        else:
            md.append("*   NAV not available.")
        md.append("")

        # ── PRIORITY 2 & 3 & 4: Expense Ratio, AUM, SIP ─────────────────────
        md.append("## Key Fees, Fund Size & Investment Details")
        md.append(f"*   **Expense Ratio:** {info['expense_ratio']}% per annum (annual management fee)")
        md.append(f"*   **Exit Load:** {info['exit_load']}")
        md.append(f"*   **Fund Size (AUM):** ₹{info['aum']:,.2f} Crores" if info["aum"] else "*   **Fund Size (AUM):** Not disclosed")
        md.append(f"*   **Minimum SIP Investment:** ₹{info['min_sip']} per month")
        md.append(f"*   **Minimum Lumpsum Investment:** ₹{info['min_lumpsum']}")
        md.append("")

        # ── PRIORITY 5: Fund Management ───────────────────────────────────────
        md.append("## Fund Management")
        if info["managers"]:
            for m in info["managers"]:
                md.append(f"### {m['name']}")
                if m["education"]:
                    md.append(f"*   **Education:** {m['education']}")
                if m["experience"]:
                    md.append(f"*   **Experience:** {m['experience']}")
        else:
            md.append("Fund manager details not available.")
        md.append("")

        # ── Holdings ──────────────────────────────────────────────────────────
        md.append("## Top Stock Holdings (by Portfolio Weight)")
        if info["holdings"]:
            md.append("| Company Name | Sector | Weight (%) |")
            md.append("| :--- | :--- | :--- |")
            for h in info["holdings"]:
                md.append(f"| {h['company_name']} | {h['sector']} | {h['percentage']}% |")
        else:
            md.append("Holdings not available.")
        md.append("")

        return "\n".join(md)

    def parse_all(self) -> dict:
        """Parse all raw HTML files and write JSON + Markdown to processed dir."""
        results = {}
        for url in config.TARGET_URLS:
            slug = url.split("/")[-1]
            raw_path = self.raw_dir / f"{slug}.html"

            if not raw_path.exists():
                logger.warning(f"Raw HTML for '{slug}' not found. Skipping.")
                continue

            try:
                info = self.parse_file(raw_path)

                json_path = self.processed_dir / f"{slug}.json"
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(info, f, indent=4)

                md_path = self.processed_dir / f"{slug}.md"
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(self.convert_to_markdown(info, url))

                logger.info(f"Processed successfully: {slug}")
                results[slug] = {"json_path": str(json_path), "md_path": str(md_path)}
            except Exception as e:
                logger.error(f"Failed to parse '{slug}': {e}")
                results[slug] = {"error": str(e)}

        return results


if __name__ == "__main__":
    parser = GrowwParser()
    parser.parse_all()
