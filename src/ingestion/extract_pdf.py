from __future__ import annotations

import json
import re
from pathlib import Path

from src.core.config import DOCUMENT_ID, DOCUMENT_TITLE, PDF_PATH, SOURCE_FILE, project_path


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("‘", "'").replace("’", "'").replace("“", '"').replace("”", '"')
    text = text.replace("–", "-").replace("—", "--")
    text = text.replace("ﬁ", "fi").replace("ﬂ", "fl")
    text = text.replace("\u00a0", " ").replace("\u00ad", "")
    text = re.sub(r"[•·▪]", "*", text)
    text = text.replace("…", "...")
    text = re.sub(r"([a-zA-Z])-\n\s*([a-zA-Z])", r"\1\2", text)
    cleaned_lines = []
    for line in text.split("\n"):
        item = line.strip()
        if not item:
            continue
        if "Downloaded from" in item:
            continue
        if re.search(r"Diabetes Care Volume \d+, Supplement \d+, [A-Za-z]+ \d{4}", item, re.I):
            continue
        if "diabetesjournals.org/care" in item:
            continue
        if re.match(r"^S\d+$", item):
            continue
        if item == "Facilitating Positive Health Behaviors and Well-being":
            continue
        cleaned_lines.append(item)
    text = "\n".join(cleaned_lines)
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def main() -> None:
    raw_pdf_path = project_path(PDF_PATH) if not Path(PDF_PATH).is_absolute() else Path(PDF_PATH)
    output_path = project_path("data", "extracted", "extracted_pages.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import fitz
    except Exception as exc:
        if output_path.exists():
            print(f"PyMuPDF is not installed ({exc}). Reusing existing extracted file: {output_path}")
            return
        print(f"Error: PyMuPDF is not installed and no extracted file exists: {exc}")
        return
    print(f"Opening PDF: {raw_pdf_path}")
    if not raw_pdf_path.exists():
        print(f"Error: PDF not found at {raw_pdf_path}")
        return
    doc = fitz.open(raw_pdf_path)
    with output_path.open("w", encoding="utf-8") as f:
        for page_num in range(len(doc)):
            raw_text = doc[page_num].get_text("text")
            record = {
                "document_id": DOCUMENT_ID,
                "source_file": SOURCE_FILE,
                "document_title": DOCUMENT_TITLE,
                "page": page_num + 1,
                "raw_text": raw_text,
                "clean_text": clean_text(raw_text),
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            if (page_num + 1) % 5 == 0 or (page_num + 1) == len(doc):
                print(f"Processed page {page_num + 1}/{len(doc)}...")
    doc.close()
    print(f"Extraction complete. Output saved to: {output_path}")


if __name__ == "__main__":
    main()
