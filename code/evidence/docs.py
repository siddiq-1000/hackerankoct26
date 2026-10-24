import base64
import zlib
import re
from pathlib import Path
from typing import Dict, List, Optional
from code.config import DATASET_DIR

class DocumentParser:
    def __init__(self, documents_dir: Optional[Path] = None):
        self.documents_dir = documents_dir or (DATASET_DIR / "evidence" / "documents")
        self._cache: Dict[str, str] = {}

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        if str(pdf_path) in self._cache:
            return self._cache[str(pdf_path)]

        if not pdf_path.exists():
            return ""

        with open(pdf_path, "rb") as f:
            full = f.read()

        idx = 0
        extracted_chunks = []
        while True:
            s_idx = full.find(b"stream", idx)
            if s_idx == -1:
                break
            e_idx = full.find(b"endstream", s_idx)
            if e_idx == -1:
                break
            stream_bytes = full[s_idx + 6:e_idx].strip()
            # Try ASCII85 + Flate/zlib decompression
            try:
                dec = base64.a85decode(stream_bytes, adobe=True)
                decomp = zlib.decompress(dec)
                if b"Tj" in decomp or b"TJ" in decomp:
                    texts = re.findall(rb"\((.*?)\)", decomp)
                    for t in texts:
                        try:
                            s = t.decode("latin1")
                            if s.strip():
                                extracted_chunks.append(s.strip())
                        except Exception:
                            pass
            except Exception:
                try:
                    decomp = zlib.decompress(stream_bytes)
                    if b"Tj" in decomp or b"TJ" in decomp:
                        texts = re.findall(rb"\((.*?)\)", decomp)
                        for t in texts:
                            try:
                                s = t.decode("latin1")
                                if s.strip():
                                    extracted_chunks.append(s.strip())
                            except Exception:
                                pass
                except Exception:
                    pass
            idx = e_idx + 9

        full_text = "\n".join(extracted_chunks)
        self._cache[str(pdf_path)] = full_text
        return full_text

    def search_terms(self, pdf_path: Path, terms: List[str]) -> List[str]:
        text = self.extract_text_from_pdf(pdf_path)
        hits = []
        for term in terms:
            if term and term.lower() in text.lower():
                hits.append(term)
        return hits
