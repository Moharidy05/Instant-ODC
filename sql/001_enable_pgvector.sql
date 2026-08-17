-- Migration 001: Enable pgvector extension
-- This extension is required to store and query vector embeddings

-- Enable pgvector extension for vector similarity search
create extension if not exists vector;
