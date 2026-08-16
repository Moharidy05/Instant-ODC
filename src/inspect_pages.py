import json
import os
from pathlib import Path

def main():
    # Define paths relative to the project root
    project_root = Path(__file__).resolve().parent.parent
    input_path = project_root / "data" / "extracted" / "extracted_pages.jsonl"
    output_dir = project_root / "data" / "extracted"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not input_path.exists():
        print(f"Error: Input file not found at {input_path}")
        return
        
    # Stats
    total_pages = 0
    total_raw_chars = 0
    total_clean_chars = 0
    empty_pages = 0
    
    pages_data = {}
    
    # Check variables for specific content
    has_table_5_1 = False
    has_table_5_2 = False
    recs_found = []
    
    # Legal note check
    has_legal_note_page_1 = False
    
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            record = json.loads(line)
            page_num = record['page']
            raw_text = record['raw_text']
            clean_text = record['clean_text']
            
            pages_data[page_num] = record
            
            total_pages += 1
            total_raw_chars += len(raw_text)
            total_clean_chars += len(clean_text)
            
            if not clean_text.strip():
                empty_pages += 1
                
            # Content checks
            if 'Table 5.1' in clean_text:
                has_table_5_1 = True
            if 'Table 5.2' in clean_text:
                has_table_5_2 = True
                
            # Check for recommendations 5.10 to 5.31
            import re
            found_recs = re.findall(r'5\.(1[0-9]|2[0-9]|3[0-1])', clean_text)
            for rec in found_recs:
                rec_str = f"5.{rec}"
                if rec_str not in recs_found:
                    recs_found.append(rec_str)
                    
            if page_num == 1:
                if 'copyright' in clean_text.lower() or 'license' in clean_text.lower() or 'rights reserved' in clean_text.lower():
                    has_legal_note_page_1 = True
                    
    # Generate sample text files for pages 1, 5, 6, 7
    target_pages = [1, 5, 6, 7]
    for p in target_pages:
        if p in pages_data:
            record = pages_data[p]
            sample_file = output_dir / f"sample_page_{p}.txt"
            with open(sample_file, 'w', encoding='utf-8') as sf:
                sf.write(f"--- METADATA ---\n")
                sf.write(f"Document ID: {record['document_id']}\n")
                sf.write(f"Source File: {record['source_file']}\n")
                sf.write(f"Title: {record['document_title']}\n")
                sf.write(f"Page: {record['page']}\n")
                sf.write(f"----------------\n\n")
                sf.write(f"=== RAW TEXT ===\n")
                sf.write(f"{record['raw_text']}\n\n")
                sf.write(f"=== CLEANED TEXT ===\n")
                sf.write(f"{record['clean_text']}\n")
            print(f"Generated sample file for page {p}: {sample_file.name}")
            
    # Generate Markdown Report
    report_file = output_dir / "extraction_sample_report.md"
    avg_chars = total_clean_chars / total_pages if total_pages > 0 else 0
    
    with open(report_file, 'w', encoding='utf-8') as rf:
        rf.write("# PDF Extraction Sample Report\n\n")
        
        rf.write("## Basic Statistics\n")
        rf.write(f"- **Total Pages Extracted:** {total_pages}\n")
        rf.write(f"- **Average Characters per Page (Cleaned):** {avg_chars:.2f}\n")
        rf.write(f"- **Total Raw Characters:** {total_raw_chars}\n")
        rf.write(f"- **Total Clean Characters:** {total_clean_chars}\n")
        rf.write(f"- **Empty Pages:** {empty_pages}\n\n")
        
        rf.write("## Quality Checks\n")
        rf.write("### 1. Is the text readable?\n")
        rf.write("> Check the `sample_page_*.txt` files to verify readability. Typically PyMuPDF yields good raw text, and the cleaning script resolves hyphenations and unusual spacing.\n\n")
        
        rf.write("### 2. Are tables extracted in a usable way?\n")
        rf.write(f"- **Table 5.1 Found:** {'Yes' if has_table_5_1 else 'No'}\n")
        rf.write(f"- **Table 5.2 Found:** {'Yes' if has_table_5_2 else 'No'}\n")
        rf.write("> PyMuPDF typically extracts tables line-by-line or cell-by-cell. For complex tables, further specialized chunking or table extraction logic (e.g., pdfplumber) might be required if the tabular structure is lost in plain text.\n\n")
        
        rf.write("### 3. Are page numbers preserved?\n")
        rf.write("> We explicitly removed standalone page numbers (e.g., 'S89') in the cleaning script to avoid breaking up the text flow. The logical page number is stored in the JSON metadata instead.\n\n")
        
        rf.write("### 4. Are nutrition recommendations visible?\n")
        rf.write(f"- **Recommendations 5.10-5.31 Found:** {sorted(recs_found) if recs_found else 'None'}\n")
        rf.write("> Check if these recommendataions appear intact in the text.\n\n")
        
        rf.write("### 5. Are there corrupted or missing parts?\n")
        rf.write("> Need manual verification of `sample_page_*.txt`, but standard cleaning handles typical Unicode and ligature issues (e.g., ﬁ, ﬂ).\n\n")
        
        rf.write("### 6. Is the PDF suitable for section-aware chunking?\n")
        rf.write("> With headers and footers removed, and hyphenation joined, the clean text is highly suitable for section-aware chunking. Distinct headers or recommendation numbers can serve as natural chunk boundaries.\n\n")
        
        rf.write("### 7. Any legal/licensing note found on page 1?\n")
        rf.write(f"- **Legal/Copyright Note on Page 1:** {'Yes' if has_legal_note_page_1 else 'No'}\n")
        
    print(f"Report generated: {report_file.name}")

if __name__ == "__main__":
    main()
