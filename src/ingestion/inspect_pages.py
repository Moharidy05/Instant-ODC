from __future__ import annotations

import json
import re

from src.core.config import project_path


def main() -> None:
    input_path = project_path("data", "extracted", "extracted_pages.jsonl")
    output_dir = project_path("data", "extracted")
    output_dir.mkdir(parents=True, exist_ok=True)
    if not input_path.exists():
        print(f"Error: Input file not found at {input_path}")
        return

    pages_data = {}
    total_pages = total_raw_chars = total_clean_chars = empty_pages = 0
    has_table_5_1 = has_table_5_2 = has_legal_note_page_1 = False
    recs_found: list[str] = []
    with input_path.open("r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            page_num = record["page"]
            raw_text = record["raw_text"]
            clean_text = record["clean_text"]
            pages_data[page_num] = record
            total_pages += 1
            total_raw_chars += len(raw_text)
            total_clean_chars += len(clean_text)
            empty_pages += 1 if not clean_text.strip() else 0
            has_table_5_1 = has_table_5_1 or "Table 5.1" in clean_text
            has_table_5_2 = has_table_5_2 or "Table 5.2" in clean_text
            for rec in re.findall(r"5\.(1[0-9]|2[0-9]|3[0-1])", clean_text):
                rec_str = f"5.{rec}"
                if rec_str not in recs_found:
                    recs_found.append(rec_str)
            if page_num == 1:
                has_legal_note_page_1 = any(term in clean_text.lower() for term in ("copyright", "license", "rights reserved"))

    for p in [1, 5, 6, 7]:
        if p not in pages_data:
            continue
        record = pages_data[p]
        sample_file = output_dir / f"sample_page_{p}.txt"
        sample_file.write_text(
            "\n".join(
                [
                    "--- METADATA ---",
                    f"Document ID: {record['document_id']}",
                    f"Source File: {record['source_file']}",
                    f"Title: {record['document_title']}",
                    f"Page: {record['page']}",
                    "----------------",
                    "",
                    "=== RAW TEXT ===",
                    record["raw_text"],
                    "",
                    "=== CLEANED TEXT ===",
                    record["clean_text"],
                ]
            ),
            encoding="utf-8",
        )
        print(f"Generated sample file for page {p}: {sample_file.name}")

    avg_chars = total_clean_chars / total_pages if total_pages else 0
    report_file = output_dir / "extraction_sample_report.md"
    report_file.write_text(
        "\n".join(
            [
                "# PDF Extraction Sample Report",
                "",
                "## Basic Statistics",
                f"- **Total Pages Extracted:** {total_pages}",
                f"- **Average Characters per Page (Cleaned):** {avg_chars:.2f}",
                f"- **Total Raw Characters:** {total_raw_chars}",
                f"- **Total Clean Characters:** {total_clean_chars}",
                f"- **Empty Pages:** {empty_pages}",
                "",
                "## Quality Checks",
                f"- **Table 5.1 Found:** {'Yes' if has_table_5_1 else 'No'}",
                f"- **Table 5.2 Found:** {'Yes' if has_table_5_2 else 'No'}",
                f"- **Recommendations 5.10-5.31 Found:** {sorted(recs_found) if recs_found else 'None'}",
                f"- **Legal/Copyright Note on Page 1:** {'Yes' if has_legal_note_page_1 else 'No'}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"Report generated: {report_file.name}")


if __name__ == "__main__":
    main()
