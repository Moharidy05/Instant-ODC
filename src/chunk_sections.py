"""
Section-Aware Chunker for Diabetes Food Safety RAG
--------------------------------------------------
This module processes extracted text from the ADA Standards of Care 
and chunks it into coherent segments optimized for Retrieval-Augmented Generation.

Key features:
1. Detects sections based on predefined headers or heuristics.
2. Generates overlapping chunks of text.
3. Respects numbered recommendation boundaries (e.g., 5.1, 5.2).
4. Classifies chunks into types (recommendation, table, safety_warning, etc.) 
   to aid retrieval.
"""

import os
import json
import re
from collections import defaultdict

INPUT_FILE = "data/extracted/extracted_pages.jsonl"
OUTPUT_FILE = "data/chunks/chunks.jsonl"

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
    "Nonnutritive sweeteners",
    "Physical Activity",
    "BEHAVIORAL STRATEGIES",
    "PSYCHOSOCIAL CARE",
    "SLEEP HEALTH",
    "TOBACCO, NICOTINE, AND E-CIGARETTE USE"
]

def load_pages(filepath):
    pages = []
    if not os.path.exists(filepath):
        print(f"Error: Input file {filepath} not found.")
        return pages
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                pages.append(json.loads(line))
    return pages

def detect_section(line):
    """
    Detect if a line is a section header.
    Matches known sections or uses heuristics for unknown headings.
    """
    line_clean = line.strip()
    line_lower = line_clean.lower()
    
    for ks in KNOWN_SECTIONS:
        if ks.lower() in line_lower:
            return ks
            
    # Heuristics: Short line, starts with uppercase, no trailing punctuation
    if 3 < len(line_clean) < 80 and line_clean[0].isupper() and not line_clean.endswith('.') and not line_clean.endswith(','):
        return line_clean
        
    return None

def determine_chunk_type(text, section_title):
    """
    Classify the chunk based on keywords and patterns in its content.
    """
    text_lower = text.lower()
    
    if re.search(r'(?<!\d)5\.\d+(?!\d)', text):
        return "recommendation"
        
    if "table 5.1" in text_lower or "table 5.2" in text_lower or (section_title and "table" in section_title.lower()):
        return "table"
        
    if any(term in text_lower for term in ["ketoacidosis", "hypoglycemia", "sglt2", "safety", "warning"]):
        return "safety_warning"
        
    if "copyright" in text_lower or "license" in text_lower or ("american diabetes association" in text_lower and len(text) < 600):
        return "citation_or_license"
        
    return "other"

def create_chunks(pages):
    chunks = []
    current_section = "Introduction"
    chunk_counter = 1
    
    current_chunk_lines = []
    current_chunk_size = 0
    
    target_min = 800
    target_max = 1200
    overlap_chars = 150
    
    for page in pages:
        page_num = page.get('page', page.get('page_num', page.get('page_start', 1)))
        text = page.get('clean_text', '')
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            detected = detect_section(line)
            if detected:
                current_section = detected
            
            is_rec_start = bool(re.match(r'^5\.\d+', line))
            
            # Conditions to flush the current chunk:
            # 1. Force break if we exceed target max.
            # 2. Min break if we reached target_min and the line starts a new sentence or paragraph (uppercase).
            # 3. Rec break if this line is the start of a numbered recommendation and we already have some text.
            force_break = current_chunk_size > target_max
            min_break = current_chunk_size >= target_min and line[0].isupper() and not is_rec_start
            rec_break = is_rec_start and current_chunk_size > 200
            
            if force_break or min_break or rec_break:
                # Finalize the current chunk
                finalize_chunk(current_chunk_lines, current_section, page_num, chunk_counter, chunks)
                chunk_counter += 1
                
                # Keep overlap to maintain context between chunks
                overlap_text = []
                overlap_size = 0
                for ol in reversed(current_chunk_lines):
                    overlap_text.insert(0, ol)
                    overlap_size += len(ol)
                    if overlap_size > overlap_chars:
                        break
                
                current_chunk_lines = overlap_text
                current_chunk_size = sum(len(x) + 1 for x in overlap_text) # +1 for space/newline
                
            current_chunk_lines.append(line)
            current_chunk_size += len(line) + 1 # +1 for space
            
    # Finalize the last chunk
    if current_chunk_lines:
        last_page = pages[-1].get('page', pages[-1].get('page_num', pages[-1].get('page_start', 1))) if pages else 1
        finalize_chunk(current_chunk_lines, current_section, last_page, chunk_counter, chunks)

    return chunks

def finalize_chunk(lines, section_title, page_num, chunk_counter, chunks_list):
    content = " ".join(lines)
    
    # Include section title for context if not already present
    if section_title and section_title.lower() not in content.lower():
        content = f"[{section_title}]\n{content}"
        
    chunk_type = determine_chunk_type(content, section_title)
    
    chunk_id = f"ada_s5_p{page_num:03d}_c{chunk_counter:03d}"
    
    chunk_data = {
        "chunk_id": chunk_id,
        "document_id": "ada_standards_2026_section_5",
        "document_title": "ADA Standards of Care in Diabetes 2026 - Section 5",
        "source_file": "dc26s005.pdf",
        "clinical_topic": "diabetes_food_safety",
        "disease_layer": "diabetes",
        "future_comorbidity_layer": None,
        "section_title": section_title,
        "page_start": page_num,
        "page_end": page_num,
        "chunk_type": chunk_type,
        "content": content,
        "citation_label": f"ADA Standards of Care in Diabetes 2026, Section 5, page {page_num}"
    }
    chunks_list.append(chunk_data)

def main():
    print("Starting section-aware chunking...")
    pages = load_pages(INPUT_FILE)
    if not pages:
        print("No pages loaded. Please ensure extraction has been run.")
        return
        
    chunks = create_chunks(pages)
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for c in chunks:
            f.write(json.dumps(c) + '\n')
            
    # Print summary statistics
    type_counts = defaultdict(int)
    section_counts = defaultdict(int)
    total_length = 0
    
    for c in chunks:
        type_counts[c['chunk_type']] += 1
        section_counts[c['section_title']] += 1
        total_length += len(c['content'])
        
    avg_length = total_length / len(chunks) if chunks else 0
    
    print(f"\n--- Chunking Summary ---")
    print(f"Total chunks: {len(chunks)}")
    print(f"Average chunk length: {avg_length:.0f} characters")
    
    print("\nChunks by Type:")
    for ct, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {ct}: {count}")
        
    print("\nChunks by Section (Top 10):")
    for sec, count in sorted(section_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {sec}: {count}")

if __name__ == "__main__":
    main()
