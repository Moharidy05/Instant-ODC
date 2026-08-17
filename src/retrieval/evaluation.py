from __future__ import annotations

import json
from pathlib import Path

from src.core.config import load_retrieval_config, project_path
from src.retrieval.retrieve import retrieve_chunks
from src.retrieval.scoring import precision_at_k


EVAL_PATH = project_path("data", "evaluation", "day2_retrieval_eval.md")
QUERIES_PATH = project_path("data", "evaluation", "test_queries.jsonl")


DEFAULT_QUERIES = [
    ("Are legumes encouraged for diabetes?", "legumes fiber eating pattern"),
    ("Can a person with diabetes drink orange juice?", "sugar sweetened beverage fruit juice"),
    ("Is water better than soda for diabetes?", "water sugar-sweetened beverages"),
    ("Are whole grains encouraged for diabetes?", "whole grains fiber carbohydrates"),
    ("Should people with diabetes avoid all fruit?", "fruit carbohydrate nutrition"),
    ("Are processed foods recommended for people with diabetes?", "processed minimally processed foods"),
    ("Is ketogenic diet safe for diabetes?", "ketogenic low carbohydrate ketoacidosis"),
    ("What protein foods are encouraged for diabetes?", "protein legumes lean plant based"),
    ("Should sodium be limited in diabetes?", "sodium salt hypertension"),
    ("Are nonnutritive sweeteners supported?", "nonnutritive sweeteners"),
    ("Is alcohol safe for diabetes?", "alcohol hypoglycemia"),
    ("What eating patterns are encouraged?", "mediterranean plant based eating patterns"),
    ("Can I eat refined grains daily?", "refined grains whole grains"),
    ("What can I drink instead of soda?", "beverages water sugar sweetened"),
    ("Are nuts and seeds encouraged?", "nuts seeds eating pattern"),
    ("Is red meat better to limit?", "red meat processed meat"),
    ("Should saturated fat be limited?", "saturated fat"),
    ("Can I use herbs instead of salt?", "sodium herbs salt"),
    ("Are vegetables encouraged?", "vegetables eating pattern"),
    ("What foods are better to limit?", "limit minimize sugar sodium processed"),
]


def _load_queries() -> list[dict]:
    if QUERIES_PATH.exists():
        rows = [json.loads(line) for line in QUERIES_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(rows) >= 20:
            return rows
    return [
        {"id": f"d2_{idx:03d}", "query": query, "expected_evidence_topic": topic, "expected_behavior": "answer_with_evidence"}
        for idx, (query, topic) in enumerate(DEFAULT_QUERIES, start=1)
    ]


def run_evaluation() -> None:
    cfg = load_retrieval_config()
    k_options = [int(k) for k in cfg.get("top_k_options", [3, 5, 8, 10])]
    max_k = max(k_options)
    rows = _load_queries()
    lines = [
        "# Day 2 Retrieval Evaluation",
        "",
        f"Queries evaluated: {len(rows)}",
        f"k values compared: {k_options}",
        "",
    ]
    for row in rows:
        query = row["query"]
        expected_topic = row.get("expected_evidence_topic") or row.get("topic") or query
        chunks = retrieve_chunks(query, top_k=max_k, candidate_k=int(cfg.get("candidate_k", 20)), log=False)
        lines.extend(
            [
                f"## {row.get('id', '')} — {query}",
                "",
                f"Expected evidence topic: {expected_topic}",
                "",
                "| k | Precision@k heuristic |",
                "|---|---:|",
            ]
        )
        for k in k_options:
            lines.append(f"| {k} | {precision_at_k(chunks, expected_topic, k):.2f} |")
        lines.extend(
            [
                "",
                "| Rank | Chunk ID | Section | Pages | Similarity | Manual relevance |",
                "|---:|---|---|---|---:|---|",
            ]
        )
        for rank, chunk in enumerate(chunks, start=1):
            pages = f"{chunk.get('page_start', '?')}-{chunk.get('page_end', '?')}"
            lines.append(
                f"| {rank} | `{chunk.get('chunk_id', '?')}` | {chunk.get('section_title', '?')} | {pages} | {float(chunk.get('similarity', 0)):.4f} | TODO |"
            )
        lines.append("")
    EVAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVAL_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"[SAVED] {EVAL_PATH}")


if __name__ == "__main__":
    run_evaluation()
