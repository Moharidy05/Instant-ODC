"""
Configuration module for the diabetes-food-safety-rag project.
Loads environment variables using python-dotenv and exposes
project-wide constants.

Provider: Google Gemini (GenAI SDK)
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ──────────────────────────────────────────────────────────────
# Supabase credentials
# ──────────────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
# The service role key should NEVER be printed or exposed to the client.
# It is used only by backend indexing scripts.
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# ──────────────────────────────────────────────────────────────
# Google Gemini configuration
# ──────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_GENERATION_MODEL = os.getenv("GEMINI_GENERATION_MODEL", "gemini-2.0-flash")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-exp-03-07")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1536"))

# ──────────────────────────────────────────────────────────────
# Project-specific constants
# ──────────────────────────────────────────────────────────────
PDF_PATH = os.getenv("PDF_PATH", "data/raw/dc26s005.pdf")
PROJECT_TOPIC = os.getenv("PROJECT_TOPIC", "diabetes_food_safety")

# Document metadata (shared across extraction, chunking, indexing)
DOCUMENT_ID = "ada_standards_2026_section_5"
DOCUMENT_TITLE = "ADA Standards of Care in Diabetes 2026 - Section 5"
