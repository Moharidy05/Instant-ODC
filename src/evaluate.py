#!/usr/bin/env python3
"""
Evaluation Runner
=================
Runs test queries from data/evaluation/test_queries.jsonl through the full
RAG pipeline (safety → retrieval → answer) and saves a structured results
report to data/evaluation/retrieval_results.md.

Usage:
    python -m src.evaluate
"""

import json
import sys
from pathlib import Path

from src.safety import classify_query
from src.retrieve import retrieve_chunks
from src.answer import generate_answer


# ──────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────

QUERIES_PATH = Path("data/evaluation/test_queries.jsonl")
RESULTS_PATH = Path("data/evaluation/retrieval_results.md")


def load_test_queries(path: Path) -> list[dict]:
    """Load test queries from JSONL file."""
    queries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                queries.append(json.loads(line))
    return queries


def run_evaluation():
    """
    Run all test queries through the pipeline and generate a results report.
    
    For each query:
    1. Classify safety
    2. Retrieve evidence chunks (if not refused)
    3. Generate answer
    4. Record results for the report
    """
    if not QUERIES_PATH.exists():
        print(f"[ERROR] Test queries file not found: {QUERIES_PATH}")
        sys.exit(1)

    queries = load_test_queries(QUERIES_PATH)
    print(f"[INFO] Loaded {len(queries)} test queries\n")

    results = []

    for q in queries:
        qid = q["id"]
        query = q["query"]
        expected = q["expected_behavior"]

        print(f"{'─'*60}")
        print(f"  [{qid}] {query}")
        print(f"  Expected: {expected}")

        # Step 1: Safety classification
        safety = classify_query(query)
        print(f"  Safety:   {safety['safety_label']} — {safety['reason']}")

        # Step 2: Retrieve chunks (skip if refused)
        chunks = []
        if safety["safety_label"] != "refuse":
            try:
                chunks = retrieve_chunks(query, top_k=5)
                print(f"  Chunks:   {len(chunks)} retrieved")
            except Exception as e:
                print(f"  Chunks:   ERROR — {e}")

        # Step 3: Generate answer
        answer = ""
        try:
            answer = generate_answer(query, chunks, safety)
            print(f"  Answer:   Generated ({len(answer)} chars)")
        except Exception as e:
            answer = f"[Error generating answer: {e}]"
            print(f"  Answer:   ERROR — {e}")

        results.append({
            "id": qid,
            "query": query,
            "expected_behavior": expected,
            "safety_label": safety["safety_label"],
            "safety_reason": safety["reason"],
            "num_chunks": len(chunks),
            "chunks": chunks,
            "answer": answer,
        })

    print(f"\n{'─'*60}")
    print(f"[INFO] All {len(results)} queries processed. Generating report...\n")

    # Generate the results report
    generate_report(results)


def generate_report(results: list[dict]):
    """Generate a markdown report from evaluation results."""
    lines = [
        "# Retrieval & Answer Evaluation Results",
        "",
        f"**Total queries evaluated:** {len(results)}",
        "",
        "---",
        "",
    ]

    for r in results:
        lines.append(f"## [{r['id']}] {r['query']}")
        lines.append("")
        lines.append(f"**Expected behavior:** `{r['expected_behavior']}`")
        lines.append(f"**Safety label:** `{r['safety_label']}` — {r['safety_reason']}")
        lines.append(f"**Chunks retrieved:** {r['num_chunks']}")
        lines.append("")

        # Show retrieved chunks
        if r["chunks"]:
            lines.append("### Retrieved Chunks")
            lines.append("")
            lines.append("| # | Chunk ID | Section | Pages | Similarity | Relevant? |")
            lines.append("|---|----------|---------|-------|------------|-----------|")
            for i, chunk in enumerate(r["chunks"], 1):
                cid = chunk.get("chunk_id", "?")
                sec = chunk.get("section_title", "?")[:40]
                pg = f"{chunk.get('page_start', '?')}-{chunk.get('page_end', '?')}"
                sim = f"{chunk.get('similarity', 0):.4f}"
                lines.append(f"| {i} | `{cid}` | {sec} | {pg} | {sim} | — |")
            lines.append("")

            # Show chunk content snippets
            lines.append("<details><summary>Chunk content previews</summary>")
            lines.append("")
            for i, chunk in enumerate(r["chunks"], 1):
                content = chunk.get("content", "")[:300]
                cite = chunk.get("citation_label", "")
                lines.append(f"**Chunk {i}** (`{chunk.get('chunk_id', '?')}`):")
                lines.append(f"> {content}...")
                lines.append(f"> *Citation: {cite}*")
                lines.append("")
            lines.append("</details>")
            lines.append("")

        # Show answer
        lines.append("### Generated Answer")
        lines.append("")
        lines.append("```")
        lines.append(r["answer"][:1500] if r["answer"] else "(no answer generated)")
        lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Summary table
    lines.insert(5, "## Summary")
    lines.insert(6, "")
    lines.insert(7, "| ID | Query (short) | Expected | Safety | Chunks | Match? |")
    lines.insert(8, "|----|---------------|----------|--------|--------|--------|")
    for i, r in enumerate(results):
        short_q = r["query"][:50] + ("..." if len(r["query"]) > 50 else "")
        match = "✅" if _behavior_matches(r) else "⚠️"
        lines.insert(9 + i,
            f"| {r['id']} | {short_q} | `{r['expected_behavior'][:20]}` "
            f"| `{r['safety_label']}` | {r['num_chunks']} | {match} |"
        )
    lines.insert(9 + len(results), "")

    # Write report
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"[SAVED] {RESULTS_PATH}")


def _behavior_matches(result: dict) -> bool:
    """Quick heuristic check if the safety label matches expected behavior."""
    expected = result["expected_behavior"]
    label = result["safety_label"]

    if "refuse" in expected and label == "refuse":
        return True
    if "evidence" in expected and label == "allowed":
        return True
    if "caution" in expected and label in ("needs_caution", "refuse"):
        return True
    if "insufficient" in expected and label in ("refuse", "needs_caution"):
        return True
    return False


# ──────────────────────────────────────────────────────────────
# Main entry point
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_evaluation()
