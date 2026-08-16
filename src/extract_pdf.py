import fitz  # PyMuPDF
import json
import re
import os
from pathlib import Path

def clean_text(text: str) -> str:
    """
    Cleans raw text extracted from the PDF based on specific rules.
    """
    if not text:
        return ""
    
    # 1. Fix Unicode characters
    # Replace smart quotes with ascii quotes
    text = text.replace('‘', "'").replace('’', "'").replace('“', '"').replace('”', '"')
    # Replace en/em dashes with standard hyphen or double hyphen
    text = text.replace('–', '-').replace('—', '--')
    # Replace ligatures
    text = text.replace('ﬁ', 'fi').replace('ﬂ', 'fl')
    # Replace non-breaking spaces with regular space
    text = text.replace('\u00a0', ' ')
    # Replace various bullet point characters with standard '*'
    text = re.sub(r'[•·▪]', '*', text)
    # Replace ellipsis character with three dots
    text = text.replace('…', '...')
    # Remove soft hyphens
    text = text.replace('\u00ad', '')
    
    # 2. Rejoin hyphenated line breaks (e.g., word-\nfragment -> wordfragment)
    # Match a lowercase/uppercase letter, hyphen, newline, optional whitespace, lowercase letter
    text = re.sub(r'([a-zA-Z])-\n\s*([a-zA-Z])', r'\1\2', text)
    
    # Process line by line for line-specific removals
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        original_line = line.strip()
        
        # Skip empty lines
        if not original_line:
            continue
            
        # 3. Remove 'Downloaded from ...' watermark lines
        # Sometimes URLs contain zero-width characters, so we do a fuzzy match or check for 'Downloaded from'
        if 'Downloaded from' in original_line:
            continue
            
        # 4. Remove repeated headers
        if re.search(r'Diabetes Care Volume \d+, Supplement \d+, [A-Za-z]+ \d{4}', original_line, re.IGNORECASE):
            continue
            
        # 5. Remove repeated footers
        if 'diabetesjournals.org/care' in original_line:
            continue
            
        # 6. Remove standalone page number lines like 'S89', 'S93'
        if re.match(r'^S\d+$', original_line):
            continue
            
        # 7. Remove standalone repeated section header
        if original_line == 'Facilitating Positive Health Behaviors and Well-being':
            continue
            
        cleaned_lines.append(original_line)
        
    # Rejoin lines
    text = '\n'.join(cleaned_lines)
    
    # 8. Collapse multiple spaces into a single space
    text = re.sub(r' {2,}', ' ', text)
    
    # 9. Collapse multiple blank lines into a single newline
    text = re.sub(r'\n{2,}', '\n', text)
    
    return text.strip()

def main():
    # Define paths relative to the project root
    project_root = Path(__file__).resolve().parent.parent
    raw_pdf_path = project_root / "data" / "raw" / "dc26s005.pdf"
    output_path = project_root / "data" / "extracted" / "extracted_pages.jsonl"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Opening PDF: {raw_pdf_path}")
    if not raw_pdf_path.exists():
        print(f"Error: PDF not found at {raw_pdf_path}")
        return
        
    doc = fitz.open(raw_pdf_path)
    total_pages = len(doc)
    print(f"Total pages: {total_pages}")
    
    # Open output file in write mode
    with open(output_path, 'w', encoding='utf-8') as f:
        for page_num in range(total_pages):
            page = doc[page_num]
            # Extract raw text
            raw_text = page.get_text("text")
            
            # Clean text
            cleaned = clean_text(raw_text)
            
            # Create JSON record
            record = {
                "document_id": "ada_standards_2026_section_5",
                "source_file": "dc26s005.pdf",
                "document_title": "ADA Standards of Care in Diabetes 2026 - Section 5",
                "page": page_num + 1,  # 1-indexed page number
                "raw_text": raw_text,
                "clean_text": cleaned
            }
            
            # Write JSON line
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
            
            # Print progress every 5 pages
            if (page_num + 1) % 5 == 0 or (page_num + 1) == total_pages:
                print(f"Processed page {page_num + 1}/{total_pages}...")
                
    doc.close()
    print(f"Extraction complete. Output saved to: {output_path}")

if __name__ == "__main__":
    main()
