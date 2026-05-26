import urllib.request
import urllib.error
import hashlib
import json
import logging
from pathlib import Path
from src import config

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class GrowwCollector:
    def __init__(self):
        self.urls = config.TARGET_URLS
        self.raw_dir = config.RAW_DATA_DIR
        self.hash_path = config.DOCUMENT_HASHES_PATH
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }
        self.hashes = self.load_hashes()

    def load_hashes(self):
        """Load document hashes from file if it exists."""
        if self.hash_path.exists():
            try:
                with open(self.hash_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading hashes: {e}")
        return {}

    def save_hashes(self):
        """Save document hashes to file."""
        try:
            with open(self.hash_path, "w", encoding="utf-8") as f:
                json.dump(self.hashes, f, indent=4)
            logger.info("Saved updated hashes successfully.")
        except Exception as e:
            logger.error(f"Error saving hashes: {e}")

    def get_slug(self, url: str) -> str:
        """Extract the fund slug from its Groww URL."""
        return url.split("/")[-1]

    def compute_hash(self, content: bytes) -> str:
        """Compute MD5 hash of raw bytes."""
        return hashlib.md5(content).hexdigest()

    def fetch_url(self, url: str) -> bytes:
        """Fetch raw HTML content of a URL."""
        logger.info(f"Fetching: {url}")
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                return response.read()
        except urllib.error.HTTPError as e:
            logger.error(f"HTTP Error {e.code} for URL {url}: {e.reason}")
            raise
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            raise

    def collect_all(self, force_update: bool = False) -> dict:
        """Collect all target URLs and save raw html if changed."""
        results = {}
        updated_count = 0
        
        for url in self.urls:
            slug = self.get_slug(url)
            file_path = self.raw_dir / f"{slug}.html"
            
            try:
                content = self.fetch_url(url)
                current_hash = self.compute_hash(content)
                old_hash = self.hashes.get(slug)
                
                # Check if file exists and hash matches
                if not force_update and file_path.exists() and old_hash == current_hash:
                    logger.info(f"Scheme '{slug}' is up-to-date. Skipping write.")
                    results[slug] = {"status": "unchanged", "path": str(file_path)}
                else:
                    logger.info(f"Writing new content for scheme '{slug}'...")
                    with open(file_path, "wb") as f:
                        f.write(content)
                    self.hashes[slug] = current_hash
                    results[slug] = {"status": "updated", "path": str(file_path)}
                    updated_count += 1
            except Exception as e:
                logger.error(f"Skipping collector for '{slug}' due to failure: {e}")
                results[slug] = {"status": "failed", "error": str(e)}

        if updated_count > 0:
            self.save_hashes()
            
        logger.info(f"Collection complete. Summary: {updated_count} files written/updated.")
        return results

if __name__ == "__main__":
    collector = GrowwCollector()
    collector.collect_all()
