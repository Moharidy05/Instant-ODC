# 🩺 Diabetes Food Safety Navigator

An evidence-based clinical RAG (Retrieval-Augmented Generation) system that answers food safety and nutrition questions for adults with diabetes, grounded exclusively in official ADA guideline content.

## Clinical Topic

**Food safety and nutrition guidance for adults with diabetes.**

This is intentionally narrow in scope:

- ✅ Food and beverage safety questions
- ✅ General nutrition recommendations
- ✅ Encouraged foods & foods to minimize
- ✅ Beverage, sodium, fiber, and carbohydrate guidance
- ✅ Eating patterns (Mediterranean, plant-based, etc.)
- ❌ NOT a diet planner
- ❌ NOT a prescription system
- ❌ NOT a meal plan generator
- ❌ NOT for insulin dosing or medication advice

## Source PDF & Credibility

|                     |                                                          |
| ------------------- | -------------------------------------------------------- |
| **Document**  | ADA Standards of Care in Diabetes — 2026                |
| **Section**   | 5. Facilitating Positive Health Behaviors and Well-being |
| **File**      | `dc26s005.pdf`                                         |
| **DOI**       | https://doi.org/10.2337/dc26-S005                        |
| **Publisher** | American Diabetes Association (ADA)                      |
| **Pages**     | S89–S131 (43 pages)                                     |

### Source Credibility and Public Usability

- The PDF is from the **American Diabetes Association Standards of Care in Diabetes 2026** — the gold standard for diabetes clinical practice recommendations.
- It is an **official clinical practice recommendation** source used worldwide by healthcare professionals.
- It is suitable for **educational, noncommercial prototype use** if properly cited and unaltered.

> ⚠️ **Legal Note:** The PDF states that text/data mining, machine learning, or similar technologies may require **prior written permission from ADA**. This should be confirmed with hackathon organizers before final submission if embeddings/RAG are applied to this document. Contact: permissions@diabetes.org

## System Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│  PDF Source   │────▶│  Extraction  │────▶│ Section-Aware    │
│ dc26s005.pdf  │     │  (PyMuPDF)   │     │ Chunking         │
└──────────────┘     └──────────────┘     └────────┬─────────┘
                                                    │
                                          ┌─────────▼─────────┐
                                          │ Gemini Embeddings  │
                                          │ gemini-embedding   │
                                          └─────────┬─────────┘
                                                    │
┌──────────────┐     ┌──────────────┐     ┌─────────▼─────────┐
│  Streamlit   │◀────│  Answer Gen  │◀────│ Supabase pgvector │
│  Frontend    │     │  (Gemini)    │     │ Vector Search     │
└──────────────┘     └──────┬───────┘     └───────────────────┘
                            │
                    ┌───────▼───────┐
                    │ Safety Layer  │
                    │ (Rule-based)  │
                    └───────────────┘
```

### Pipeline Steps

1. **PDF Extraction** — Extract text page-by-page using PyMuPDF, clean artifacts
2. **Section-Aware Chunking** — Split into overlapping chunks with section metadata
3. **Embedding Generation** — Generate vectors using Google Gemini embedding model
4. **Supabase pgvector Indexing** — Store chunks and embeddings with full metadata
5. **Retrieval** — Cosine similarity search filtered by clinical topic and disease layer
6. **Safety Layer** — Rule-based classification (allowed / caution / refuse)
7. **Grounded Answer Generation** — LLM answers only from retrieved evidence
8. **Streamlit Demo** — Interactive UI with visible evidence chunks and citations

## Project Structure

```
diabetes-food-safety-rag/
├── app.py                              # Streamlit application
├── requirements.txt                    # Python dependencies
├── .env.example                        # Environment variable template
├── README.md                           # This file
│
├── data/
│   ├── raw/
│   │   └── dc26s005.pdf                # Source guideline PDF
│   ├── extracted/
│   │   ├── extracted_pages.jsonl       # Page-level extracted text
│   │   ├── extraction_sample_report.md # Extraction quality report
│   │   └── sample_page_*.txt           # Sample page inspections
│   ├── chunks/
│   │   └── chunks.jsonl                # Section-aware chunks with metadata
│   └── evaluation/
│       ├── test_queries.jsonl           # 10 test queries
│       └── retrieval_results.md         # Evaluation results report
│
├── src/
│   ├── __init__.py
│   ├── config.py                       # Environment config loader
│   ├── extract_pdf.py                  # PDF text extraction
│   ├── inspect_pages.py                # Sample page inspection
│   ├── chunk_sections.py               # Section-aware chunking
│   ├── embeddings.py                   # Gemini embedding wrapper
│   ├── supabase_client.py              # Supabase client initialization
│   ├── index_supabase.py               # Chunk indexing to Supabase
│   ├── retrieve.py                     # Vector similarity retrieval
│   ├── answer.py                       # Grounded answer generation
│   ├── safety.py                       # Query safety classification
│   ├── prompts.py                      # LLM prompt templates
│   └── evaluate.py                     # Test query evaluation runner
│
└── sql/
    ├── 001_enable_pgvector.sql         # Enable pgvector extension
    ├── 002_create_tables.sql           # Create documents & chunks tables
    └── 003_match_chunks_function.sql   # Cosine similarity search function
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd diabetes-food-safety-rag
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your actual credentials
```

You need:

- **Supabase** project credentials (see below)
- **Google Gemini** API key (get from [Google AI Studio](https://aistudio.google.com/apikey))

### 3. Set Up Supabase

#### Where to Get Supabase Credentials

1. Create a free project at [supabase.com](https://supabase.com)
2. Open your project dashboard
3. Go to **Project Settings → API** (or use the Connect dialog)
4. Copy **Project URL** → paste into `SUPABASE_URL`
5. Copy **anon/public key** → paste into `SUPABASE_ANON_KEY`
6. Copy **service_role/secret key** → paste into `SUPABASE_SERVICE_ROLE_KEY`

> ⚠️ **Security:**
>
> - Never expose the service role key in frontend code
> - Never commit `.env` to git — commit only `.env.example`
> - The service role key is used only by backend indexing scripts

#### Run SQL Migrations

In the Supabase SQL Editor, run these files in order:

```sql
-- 1. Enable pgvector
-- Run contents of sql/001_enable_pgvector.sql

-- 2. Create tables
-- Run contents of sql/002_create_tables.sql

-- 3. Create match function
-- Run contents of sql/003_match_chunks_function.sql
```

### 4. Extract PDF Text

```bash
python -m src.extract_pdf
```

Output: `data/extracted/extracted_pages.jsonl`

### 5. Inspect Sample Pages

```bash
python -m src.inspect_pages
```

Output: Sample text files and `data/extracted/extraction_sample_report.md`

### 6. Create Chunks

```bash
python -m src.chunk_sections
```

Output: `data/chunks/chunks.jsonl`

### 7. Index Chunks to Supabase

```bash
python -m src.index_supabase
```

This generates embeddings and upserts all chunks to Supabase.

### 8. Run Test Queries (Optional)

```bash
python -m src.evaluate
```

Output: `data/evaluation/retrieval_results.md`

### 9. Launch Streamlit App

```bash
streamlit run app.py
```

## Disease Layer Architecture

The system is designed for future multi-disease support:

| Layer                             | Status      | Guideline                     |
| --------------------------------- | ----------- | ----------------------------- |
| Diabetes                          | ✅ Active   | ADA Standards 2026, Section 5 |
| Diabetes + Kidney Disease         | 🔒 Prepared | Pending guideline PDF         |
| Diabetes + Cardiovascular Disease | 🔒 Prepared | Pending guideline PDF         |
| Diabetes + Pregnancy              | 🔒 Prepared | Pending guideline PDF         |
| Diabetes + Hypertension           | 🔒 Prepared | Pending guideline PDF         |

To add a new disease layer:

1. Add the guideline PDF to `data/raw/`
2. Extract and chunk with appropriate `disease_layer` and `clinical_topic` metadata
3. Index to Supabase — the existing schema supports multiple layers
4. Update the active layers in `app.py`

## Safety Layer

The system classifies every query before processing:

| Classification    | Action                      | Example                                 |
| ----------------- | --------------------------- | --------------------------------------- |
| `allowed`       | Answer with evidence        | "Are legumes encouraged for diabetes?"  |
| `needs_caution` | Answer with caution framing | "How many grams of carbs should I eat?" |
| `refuse`        | Refuse and explain          | "How much insulin should I take?"       |

Refused categories:

- Insulin dosing
- Medication adjustment
- Emergency treatment
- Full meal plans with exact grams
- Comorbidity advice without matching guideline loaded

## License & Disclaimer

This is a **hackathon prototype for educational purposes only**.

- Source content © 2025 American Diabetes Association
- Not intended for clinical decision-making
- Not a substitute for professional medical advice
- For individualized nutrition therapy, consult a qualified clinician or registered dietitian
