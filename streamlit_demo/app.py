from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from src.answering.answer import full_pipeline
from src.core.config import MIN_RETRIEVAL_CONFIDENCE, PROJECT_TOPIC, RETRIEVAL_TOP_K, project_path
from src.food.food_lists import build_food_guidance_lists
from src.layers.disease_layer_orchestrator import layer_status_rows, orchestrate_disease_layer
from src.retrieval.retrieve import local_retrieve_chunks, retrieve_chunks
from src.safety.safety import SAFETY_NOTE


def _load_all_chunks() -> list[dict]:
    path = project_path("data", "chunks", "chunks.jsonl")
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _chunk_card(chunk: dict, rank: int | None = None) -> None:
    prefix = f"#{rank} " if rank else ""
    sim = float(chunk.get("similarity", 0.0) or 0.0)
    with st.expander(
        f"{prefix}{chunk.get('chunk_id', '?')} — {chunk.get('section_title', 'Unknown')} "
        f"(p.{chunk.get('page_start', '?')}) — similarity {sim:.3f}",
        expanded=rank is not None and rank <= 2,
    ):
        st.write(
            {
                "chunk_id": chunk.get("chunk_id"),
                "section": chunk.get("section_title"),
                "page_start": chunk.get("page_start"),
                "page_end": chunk.get("page_end"),
                "chunk_type": chunk.get("chunk_type"),
                "disease_layer": chunk.get("disease_layer"),
                "citation": chunk.get("citation_label"),
                "similarity": sim,
            }
        )
        st.markdown((chunk.get("content", "") or "")[:1200])


def main() -> None:
    st.set_page_config(page_title="Diabetes Food Safety Navigator", page_icon="🩺", layout="wide")
    st.title("Diabetes Food Safety Navigator")
    st.caption("Evidence-grounded RAG for adult diabetes food safety questions. Not a diet planner or prescription system.")

    ask_tab, list_tab, explorer_tab, eval_tab, layers_tab = st.tabs(
        ["Ask", "Food Guidance List", "Evidence Explorer", "Evaluation", "Disease Layers"]
    )

    with ask_tab:
        examples = [
            "Can a person with diabetes drink orange juice?",
            "Are legumes encouraged for diabetes?",
            "Is water better than soda for diabetes?",
            "Are processed foods recommended for people with diabetes?",
            "How much insulin should I take after eating rice?",
            "I have diabetes and kidney disease. Can I eat bananas daily?",
            "Who won the world cup?",
        ]
        selected_example = st.selectbox("Safety demo examples", [""] + examples)
        query = st.text_input("Question", value=selected_example, placeholder="Can I eat this as a person with diabetes?")
        selected_layer = st.selectbox(
            "Disease layer",
            ["diabetes", "diabetes + kidney disease", "diabetes + cardiovascular disease", "diabetes + pregnancy", "diabetes + hypertension"],
        )
        top_k = st.slider("Top-k evidence chunks", min_value=3, max_value=10, value=RETRIEVAL_TOP_K)

        if st.button("Retrieve evidence and answer", type="primary") and query.strip():
            result = full_pipeline(
                query=query,
                clinical_topic=PROJECT_TOPIC,
                disease_layer=selected_layer,
                top_k=top_k,
            )
            safety = result["safety_result"]
            confidence = result["confidence"]
            st.subheader("Safety classification")
            st.write(safety)
            st.subheader("Disease layer routing")
            st.write(result["layer"])
            st.subheader("Retrieval confidence")
            st.write(
                {
                    "status": confidence["status"],
                    "top_similarity": round(confidence["top_similarity"], 3),
                    "top_lexical_overlap": confidence.get("top_lexical_overlap"),
                    "threshold": MIN_RETRIEVAL_CONFIDENCE,
                }
            )

            st.subheader("Retrieved chunks")
            if result["chunks"]:
                for idx, chunk in enumerate(result["chunks"], start=1):
                    _chunk_card(chunk, idx)
            else:
                st.info("No chunks retrieved or retrieval skipped due to safety/layer refusal.")

            st.subheader("Final answer")
            if safety.get("safety_label") == "refuse":
                st.error(safety.get("reason", "Request refused."))
            st.markdown(result["answer"])

            if result["substitutions"]:
                st.subheader("Suggested alternatives tied to retrieved evidence")
                st.table(result["substitutions"])

            with st.expander("Citation validation"):
                st.write(result["citation_validation"])

            with st.expander("Unsupported claims"):
                unsupported = result.get("unsupported_claims", [])
                if unsupported:
                    st.write(unsupported)
                else:
                    st.success("No unsupported claims flagged.")

        st.warning(SAFETY_NOTE)

    with list_tab:
        st.subheader("Food guidance list")
        chunks = _load_all_chunks()
        lists = build_food_guidance_lists(chunks)
        for category, rows in lists.items():
            st.markdown(f"### {category}")
            if rows:
                st.table(rows)
            else:
                st.caption("No local evidence-linked items found yet. Index or inspect chunks first.")

    with explorer_tab:
        st.subheader("Evidence explorer")
        chunks = _load_all_chunks()
        section_options = sorted({c.get("section_title", "") for c in chunks if c.get("section_title")})
        chunk_type_options = sorted({c.get("chunk_type", "") for c in chunks if c.get("chunk_type")})
        col1, col2, col3 = st.columns(3)
        with col1:
            search = st.text_input("Search chunks")
        with col2:
            section = st.selectbox("Section", [""] + section_options)
        with col3:
            chunk_type = st.selectbox("Chunk type", [""] + chunk_type_options)
        page_filter = st.text_input("Page filter", placeholder="e.g. 6")
        filtered = []
        for chunk in chunks:
            if section and chunk.get("section_title") != section:
                continue
            if chunk_type and chunk.get("chunk_type") != chunk_type:
                continue
            if page_filter and str(chunk.get("page_start")) != page_filter:
                continue
            if search and search.lower() not in " ".join([chunk.get("content", ""), chunk.get("section_title", "")]).lower():
                continue
            filtered.append(chunk)
        st.caption(f"{len(filtered)} matching chunks")
        for chunk in filtered[:30]:
            _chunk_card(chunk)

    with eval_tab:
        st.subheader("Evaluation")
        st.write("Run evaluation scripts from the terminal:")
        st.code("python3 -m src.retrieval.evaluation\npython3 -m src.evaluate")
        for rel in [
            "data/evaluation/day2_retrieval_eval.md",
            "data/evaluation/day3_generation_eval.md",
            "data/evaluation/day4_safety_eval.md",
            "data/evaluation/retrieval_results.md",
        ]:
            path = project_path(rel)
            if path.exists():
                with st.expander(rel):
                    st.markdown(path.read_text(encoding="utf-8")[:10000])

    with layers_tab:
        st.subheader("Disease layers")
        rows = layer_status_rows()
        st.table(rows)
        st.write("Layer routing preview")
        q = st.text_input("Preview query", value="I have diabetes and kidney disease. Can I eat bananas daily?")
        selected = st.selectbox("Selected layer for preview", ["diabetes", "diabetes + kidney disease"], key="layer_preview")
        st.json(orchestrate_disease_layer(q, selected))


if __name__ == "__main__":
    main()
