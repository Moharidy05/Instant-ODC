-- ============================================================
-- DEV ONLY: Reset all tables for re-indexing.
-- Do NOT run this in production.
-- Use this when changing embedding dimensions or re-indexing.
-- ============================================================

drop table if exists retrieval_logs cascade;
drop table if exists food_substitutions cascade;
drop table if exists food_guidance_rules cascade;
drop table if exists food_items cascade;
drop table if exists guideline_chunks cascade;
drop table if exists documents cascade;
