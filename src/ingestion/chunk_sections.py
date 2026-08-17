from __future__ import annotations

import json
import re
from collections import defaultdict

from src.core.config import DOCUMENT_ID, DOCUMENT_TITLE, PROJECT_TOPIC, SOURCE_FILE, load_retrieval_config, project_path


INPUT_FILE = project_path("data", "extracted", "extracted_pages.jsonl")
OUTPUT_FILE = project_path("data", "chunks", "chunks.jsonl")

KNOWN_SECTIONS = [
    "DIABETES SELF-MANAGEMENT EDUCATION AND SUPPORT",
    "MEDICAL NUTRITION THERAPY",
    "Table 5.1—Nutrition recommendations",
    "Table 5.1--Nutrition recommendations",
    "Table 5.2—Nutrition behaviors to encourage",
    "Table 5.2-Nutrition behaviors",
    "Eating Patterns and Meal Planning",
    "Carbohydrates",
    "Protein",
    "Fats",
    "Sodium",
    "Alcohol",
    "Nonnutritive Sweeteners",
    "Physical Activity",
    "BEHAVIORAL STRATEGIES",
    "PSYCHOSOCIAL CARE",
    "SLEEP HEALTH",
    "TOBACCO, NICOTINE, AND E-CIGARETTE USE",
]


def load_pages(filepath=INPUT_FILE) -> list[dict]:
    if not filepath.exists():
        print(f"Error: Input file {filepath} not found.")
        return []
    return [json.loads(line) for line in filepath.read_text(encoding="utf-8").splitlines() if line.strip()]


def detect_section(line: str) -> str | None:
    line_clean = line.strip()
    line_lower = line_clean.lower()
    for section in KNOWN_SECTIONS:
        if section.lower() in line_lower:
            return section
    if 3 < len(line_clean) < 80 and line_clean[0].isupper() and not line_clean.endswith((".", ",")):
        return line_clean
    return None


def determine_chunk_type(text: str, section_title: str) -> str:
    text_lower = text.lower()
    if re.search(r"(?<!\d)5\.\d+(?!\d)", text):
        return "recommendation"
    if "table 5.1" in text_lower or "table 5.2" in text_lower or ("table" in (section_title or "").lower()):
        return "table"
    if any(term in text_lower for term in ["ketoacidosis", "hypoglycemia", "sglt2", "safety", "warning"]):
        return "safety_warning"
    if "copyright" in text_lower or "license" in text_lower:
        return "citation_or_license"
    return "other"


def create_chunks(pages: list[dict]) -> list[dict]:
    cfg = load_retrieval_config()
    target_min = int(cfg["chunk_target_min"])
    target_max = int(cfg["chunk_target_max"])
    overlap_chars = int(cfg["overlap_chars"])
    chunks: list[dict] = []
    current_section = "Introduction"
    chunk_counter = 1
    current_chunk_lines: list[str] = []
    current_chunk_size = 0

    for page in pages:
        page_num = page.get("page", page.get("page_num", page.get("page_start", 1)))
        for raw_line in page.get("clean_text", "").split("\n"):
            line = raw_line.strip()
            if not line:
                continue
            detected = detect_section(line)
            if detected:
                current_section = detected
            is_rec_start = bool(re.match(r"^5\.\d+", line))
            force_break = current_chunk_size > target_max
            min_break = current_chunk_size >= target_min and line[0].isupper() and not is_rec_start
            rec_break = is_rec_start and current_chunk_size > 200
            if current_chunk_lines and (force_break or min_break or rec_break):
                finalize_chunk(current_chunk_lines, current_section, page_num, chunk_counter, chunks)
                chunk_counter += 1
                overlap_text: list[str] = []
                overlap_size = 0
                for ol in reversed(current_chunk_lines):
                    overlap_text.insert(0, ol)
                    overlap_size += len(ol)
                    if overlap_size > overlap_chars:
                        break
                current_chunk_lines = overlap_text
                current_chunk_size = sum(len(x) + 1 for x in overlap_text)
            current_chunk_lines.append(line)
            current_chunk_size += len(line) + 1

    if current_chunk_lines:
        last_page = pages[-1].get("page", 1) if pages else 1
        finalize_chunk(current_chunk_lines, current_section, last_page, chunk_counter, chunks)
    return chunks


def finalize_chunk(lines: list[str], section_title: str, page_num: int, chunk_counter: int, chunks_list: list[dict]) -> None:
    content = " ".join(lines)
    if section_title and section_title.lower() not in content.lower():
        content = f"[{section_title}]\n{content}"
    chunk_id = f"ada_s5_p{page_num:03d}_c{chunk_counter:03d}"
    chunks_list.append(
        {
            "chunk_id": chunk_id,
            "document_id": DOCUMENT_ID,
            "document_title": DOCUMENT_TITLE,
            "source_file": SOURCE_FILE,
            "clinical_topic": PROJECT_TOPIC,
            "disease_layer": "diabetes",
            "future_comorbidity_layer": None,
            "section_title": section_title,
            "page_start": page_num,
            "page_end": page_num,
            "chunk_type": determine_chunk_type(content, section_title),
            "content": content,
            "citation_label": f"ADA Standards of Care in Diabetes 2026, Section 5, page {page_num}",
        }
    )


def main() -> None:
    print("Starting section-aware chunking...")
    pages = load_pages()
    if not pages:
        print("No pages loaded. Please ensure extraction has been run.")
        return
    chunks = create_chunks(pages)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    type_counts = defaultdict(int)
    section_counts = defaultdict(int)
    total_length = 0
    for chunk in chunks:
        type_counts[chunk["chunk_type"]] += 1
        section_counts[chunk["section_title"]] += 1
        total_length += len(chunk["content"])
    avg_length = total_length / len(chunks) if chunks else 0
    print("\n--- Chunking Summary ---")
    print(f"Total chunks: {len(chunks)}")
    print(f"Average chunk length: {avg_length:.0f} characters")
    print("\nChunks by Type:")
    for chunk_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {chunk_type}: {count}")
    print("\nChunks by Section (Top 10):")
    for section, count in sorted(section_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {section}: {count}")


if __name__ == "__main__":
    main()
