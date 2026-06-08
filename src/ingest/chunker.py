import json
import logging
from pathlib import Path
from datetime import datetime
from src import config

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class MetadataChunker:
    def __init__(self):
        self.processed_dir = config.PROCESSED_DATA_DIR
        self.chunk_size = config.CHUNK_SIZE * 4      # Approx 4 characters per token
        self.chunk_overlap = config.CHUNK_OVERLAP * 4 # Approx 4 characters per token

    def extract_metadata_from_md(self, content: str) -> dict:
        """Extract metadata variables from the top header of our generated markdown."""
        metadata = {
            "source_url": "",
            "scheme_name": "",
            "document_type": "Groww Scheme Page",
            "last_updated_date": datetime.today().strftime('%d-%b-%Y')
        }
        
        lines = content.split("\n")
        for line in lines:
            if line.startswith("# Scheme Profile:"):
                metadata["scheme_name"] = line.replace("# Scheme Profile:", "").strip()
            elif line.startswith("**Source Citation URL:**"):
                metadata["source_url"] = line.replace("**Source Citation URL:**", "").strip()
                
        return metadata

    def split_text_recursive(self, text: str, max_chars: int, overlap_chars: int) -> list:
        """Lightweight split algorithm using paragraph/newline markers to preserve formatting."""
        chunks = []
        # First try splitting by double newline (paragraphs/sections)
        paragraphs = text.split("\n\n")
        
        current_chunk = []
        current_len = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            para_len = len(para)
            
            # If a single paragraph is too large, split it by line or force character splits
            if para_len > max_chars:
                # If we have gathered some text, flush it
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = []
                    current_len = 0
                
                # Split large paragraph by line
                lines = para.split("\n")
                sub_chunk = []
                sub_len = 0
                for line in lines:
                    line_len = len(line)
                    if sub_len + line_len > max_chars:
                        if sub_chunk:
                            chunks.append("\n".join(sub_chunk))
                            # Keep overlap
                            overlap_str = "\n".join(sub_chunk)[-overlap_chars:]
                            sub_chunk = [overlap_str, line]
                            sub_len = len(overlap_str) + line_len
                        else:
                            # Force chunking of extremely long line
                            for i in range(0, line_len, max_chars - overlap_chars):
                                chunks.append(line[i:i + max_chars])
                    else:
                        sub_chunk.append(line)
                        sub_len += line_len + 1
                if sub_chunk:
                    chunks.append("\n".join(sub_chunk))
            
            elif current_len + para_len > max_chars:
                # Flush current chunk
                chunks.append("\n\n".join(current_chunk))
                
                # Keep sliding window overlap
                overlap_text = "\n\n".join(current_chunk)[-overlap_chars:]
                current_chunk = [overlap_text, para]
                current_len = len(overlap_text) + para_len + 2
            else:
                current_chunk.append(para)
                current_len += para_len + 2 # accounts for double newlines
                
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))
            
        return chunks

    def chunk_all(self) -> list:
        """Chunk all processed markdown profiles and output a single unified chunks.json."""
        logger.info("Starting chunking process...")
        all_chunks = []
        
        md_files = list(self.processed_dir.glob("*.md"))
        logger.info(f"Found {len(md_files)} markdown scheme profiles to chunk.")
        
        for md_path in md_files:
            logger.info(f"Chunking: {md_path.name}")
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()

            metadata = self.extract_metadata_from_md(content)
            
            # Split the text
            text_splits = self.split_text_recursive(content, self.chunk_size, self.chunk_overlap)
            logger.info(f"Created {len(text_splits)} splits for {md_path.name}")
            
            for idx, text_chunk in enumerate(text_splits):
                # Tag chunk with specific section header if possible
                page_section = "General Overview"
                for line in text_chunk.split("\n"):
                    if line.startswith("## "):
                        page_section = line.replace("## ", "").strip()
                        break
                        
                chunk_data = {
                    "chunk_id": f"{md_path.stem}_chunk_{idx}",
                    "text": text_chunk,
                    "metadata": {
                        "source_url": metadata["source_url"],
                        "scheme_name": metadata["scheme_name"],
                        "document_type": metadata["document_type"],
                        "page_section": page_section,
                        "last_updated_date": metadata["last_updated_date"]
                    }
                }
                all_chunks.append(chunk_data)

        # Save unified chunks
        output_path = self.processed_dir / "chunks.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_chunks, f, indent=4)
            
        logger.info(f"Saved {len(all_chunks)} total chunks to {output_path}")
        return all_chunks

if __name__ == "__main__":
    chunker = MetadataChunker()
    chunker.chunk_all()
