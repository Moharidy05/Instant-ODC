#!/usr/bin/env python3
"""
Diabetes Food Safety Navigator — Streamlit App
================================================
Evidence-based food safety assistant for adults with diabetes.
Answers questions only from official ADA guideline content.

Usage:
    streamlit run app.py
"""

import streamlit as st
from src.safety import classify_query
from src.retrieve import retrieve_chunks
from src.answer import generate_answer


# ──────────────────────────────────────────────────────────────
# Page Configuration
# ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Diabetes Food Safety Navigator",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────
# Custom CSS for a clean clinical look
# ──────────────────────────────────────────────────────────────

st.markdown("""
<style>
    /* Main container */
    .main .block-container {
        max-width: 1100px;
        padding-top: 2rem;
    }

    /* Header styling */
    .app-header {
        background: linear-gradient(135deg, #1a365d 0%, #2d5a87 50%, #3182ce 100%);
        padding: 2rem 2.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        color: white;
    }
    .app-header h1 {
        color: white !important;
        font-size: 2rem;
        margin-bottom: 0.3rem;
    }
    .app-header p {
        color: #bee3f8;
        font-size: 1rem;
        margin: 0;
    }

    /* Chunk cards */
    .chunk-card {
        background: #f7fafc;
        border-left: 4px solid #3182ce;
        padding: 1rem 1.2rem;
        border-radius: 0 8px 8px 0;
        margin-bottom: 0.8rem;
        font-size: 0.9rem;
    }
    .chunk-card .chunk-meta {
        color: #718096;
        font-size: 0.78rem;
        margin-bottom: 0.4rem;
    }
    .chunk-card .chunk-sim {
        background: #ebf8ff;
        color: #2b6cb0;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    /* Safety badges */
    .safety-allowed {
        background: #c6f6d5; color: #22543d;
        padding: 4px 12px; border-radius: 16px;
        font-weight: 600; font-size: 0.85rem;
    }
    .safety-caution {
        background: #fefcbf; color: #744210;
        padding: 4px 12px; border-radius: 16px;
        font-weight: 600; font-size: 0.85rem;
    }
    .safety-refuse {
        background: #fed7d7; color: #9b2c2c;
        padding: 4px 12px; border-radius: 16px;
        font-weight: 600; font-size: 0.85rem;
    }

    /* Sidebar */
    .sidebar .sidebar-content {
        background: #f7fafc;
    }

    /* Answer box */
    .answer-box {
        background: #f0fff4;
        border: 1px solid #c6f6d5;
        border-radius: 8px;
        padding: 1.5rem;
        margin-top: 1rem;
    }

    /* Disclaimer */
    .disclaimer {
        background: #fffbeb;
        border: 1px solid #fefcbf;
        border-radius: 8px;
        padding: 1rem;
        font-size: 0.82rem;
        color: #744210;
        margin-top: 1rem;
    }

    /* Disease layer badges */
    .layer-active {
        background: #c6f6d5; color: #22543d;
        padding: 3px 10px; border-radius: 12px;
        font-size: 0.8rem; font-weight: 600;
    }
    .layer-inactive {
        background: #e2e8f0; color: #718096;
        padding: 3px 10px; border-radius: 12px;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────────────────────

st.markdown("""
<div class="app-header">
    <h1>🩺 Diabetes Food Safety Navigator</h1>
    <p>Evidence-based food safety guidance grounded in ADA Standards of Care 2026</p>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### ⚙️ Settings")

    clinical_topic = st.selectbox(
        "Clinical Topic",
        ["diabetes_food_safety"],
        index=0,
        help="The clinical topic to search within."
    )

    st.markdown("---")
    st.markdown("### 🏥 Disease Layer")

    disease_layer = st.radio(
        "Select disease context:",
        [
            "diabetes",
            "diabetes + kidney disease",
            "diabetes + cardiovascular disease",
            "diabetes + pregnancy",
            "diabetes + hypertension",
        ],
        index=0,
    )

    # Show status for each layer
    ACTIVE_LAYERS = {"diabetes"}
    if disease_layer not in ACTIVE_LAYERS:
        st.warning(
            f"**Coming soon.** The `{disease_layer}` layer is prepared in "
            f"the architecture but not active because its official guideline "
            f"PDF has not been indexed yet."
        )
        # Fall back to base diabetes layer
        effective_layer = "diabetes"
    else:
        effective_layer = disease_layer

    st.markdown("---")

    # Layer status display
    st.markdown("**Layer Status:**")
    layers_status = {
        "diabetes": True,
        "diabetes + kidney disease": False,
        "diabetes + cardiovascular disease": False,
        "diabetes + pregnancy": False,
        "diabetes + hypertension": False,
    }
    for layer_name, active in layers_status.items():
        badge = "layer-active" if active else "layer-inactive"
        icon = "✅" if active else "🔒"
        st.markdown(
            f'{icon} <span class="{badge}">{layer_name}</span>',
            unsafe_allow_html=True
        )

    st.markdown("---")

    top_k = st.slider(
        "Evidence chunks to retrieve",
        min_value=1, max_value=10, value=5,
        help="Number of relevant guideline chunks to retrieve."
    )

    show_raw = st.checkbox("Show raw chunk text", value=True)

    st.markdown("---")
    st.markdown(
        "<div class='disclaimer'>"
        "📋 <b>Source:</b> ADA Standards of Care in Diabetes 2026, Section 5.<br>"
        "This tool is for educational purposes only."
        "</div>",
        unsafe_allow_html=True
    )


# ──────────────────────────────────────────────────────────────
# Main Query Interface
# ──────────────────────────────────────────────────────────────

st.markdown("### 💬 Ask a food safety question")

# Example queries
with st.expander("📝 Example questions you can ask"):
    examples = [
        "Can a person with diabetes drink orange juice?",
        "Is water better than soda for diabetes?",
        "Are legumes encouraged for people with diabetes?",
        "Is brown rice or whole grain food encouraged for diabetes?",
        "Should people with diabetes avoid all fruit?",
        "Is a ketogenic diet safe for diabetes?",
        "Are processed foods recommended for people with diabetes?",
    ]
    for ex in examples:
        if st.button(ex, key=f"ex_{ex[:20]}"):
            st.session_state["query_input"] = ex

# Query input
query = st.text_input(
    "Your question:",
    value=st.session_state.get("query_input", ""),
    placeholder="e.g., Can a person with diabetes drink orange juice?",
    key="query_box",
)

retrieve_btn = st.button("🔍 Retrieve Evidence & Answer", type="primary", use_container_width=True)


# ──────────────────────────────────────────────────────────────
# Processing Pipeline
# ──────────────────────────────────────────────────────────────

if retrieve_btn and query.strip():
    with st.spinner("Analyzing query safety..."):
        safety_result = classify_query(query)

    # Display safety classification
    label = safety_result["safety_label"]
    badge_class = {
        "allowed": "safety-allowed",
        "needs_caution": "safety-caution",
        "refuse": "safety-refuse",
    }.get(label, "safety-caution")

    st.markdown(f"""
    <div style="margin: 1rem 0;">
        <span class="{badge_class}">Safety: {label.upper()}</span>
        &nbsp;&nbsp;<span style="color: #718096; font-size: 0.85rem;">{safety_result['reason']}</span>
    </div>
    """, unsafe_allow_html=True)

    # If refused, show refusal message and stop
    if label == "refuse":
        st.error(f"⛔ **Query refused:** {safety_result['reason']}")
        st.info(
            "This system cannot provide advice on insulin dosing, medication "
            "adjustment, full meal plans, emergency care, or comorbidity-specific "
            "advice without a matching guideline loaded. Please consult a "
            "qualified clinician."
        )
    else:
        # Retrieve evidence chunks
        chunks = []
        with st.spinner(f"Retrieving top {top_k} evidence chunks..."):
            try:
                chunks = retrieve_chunks(
                    query,
                    clinical_topic=clinical_topic,
                    disease_layer=effective_layer,
                    top_k=top_k,
                )
            except Exception as e:
                st.error(f"Retrieval error: {e}")

        if chunks:
            # Display retrieved chunks
            st.markdown(f"### 📚 Retrieved Evidence ({len(chunks)} chunks)")

            for i, chunk in enumerate(chunks, 1):
                sim_pct = f"{chunk.get('similarity', 0) * 100:.1f}%"
                with st.expander(
                    f"Chunk {i}: {chunk.get('section_title', 'Unknown section')} "
                    f"(p.{chunk.get('page_start', '?')}) — similarity: {sim_pct}",
                    expanded=(i <= 2),  # Auto-expand first 2
                ):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1:
                        st.markdown(f"**Chunk ID:** `{chunk.get('chunk_id', '?')}`")
                        st.markdown(f"**Section:** {chunk.get('section_title', '?')}")
                    with col2:
                        st.markdown(f"**Pages:** {chunk.get('page_start', '?')}–{chunk.get('page_end', '?')}")
                        st.markdown(f"**Type:** `{chunk.get('chunk_type', '?')}`")
                    with col3:
                        st.markdown(f"**Similarity:** `{sim_pct}`")
                        st.markdown(f"**Layer:** `{chunk.get('disease_layer', '?')}`")

                    if show_raw:
                        st.markdown("---")
                        st.markdown(chunk.get("content", "*(no content)*"))

                    st.caption(f"📎 {chunk.get('citation_label', '')}")

            # Generate answer
            st.markdown("### 🩺 Generated Answer")

            with st.spinner("Generating evidence-based answer..."):
                try:
                    answer = generate_answer(query, chunks, safety_result)
                    st.markdown(
                        f'<div class="answer-box">{answer}</div>',
                        unsafe_allow_html=True,
                    )
                except Exception as e:
                    st.error(f"Answer generation error: {e}")
                    st.markdown("*Could not generate answer. Check your Gemini API key.*")

            # Citations
            st.markdown("### 📎 Citations")
            seen_citations = set()
            for chunk in chunks:
                cite = chunk.get("citation_label", "")
                if cite and cite not in seen_citations:
                    st.markdown(f"- {cite}")
                    seen_citations.add(cite)

        else:
            st.warning("No evidence chunks retrieved. The vector store may not be indexed yet.")

        # Safety note
        st.markdown("""
        <div class="disclaimer">
            ⚠️ <b>Safety Note:</b> This is not a personalized diet plan or medical
            prescription. For individualized nutrition therapy, consult a qualified
            clinician or registered dietitian. This tool provides guideline-grounded
            information for educational purposes only.
        </div>
        """, unsafe_allow_html=True)

elif retrieve_btn:
    st.warning("Please enter a question first.")


# ──────────────────────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #a0aec0; font-size: 0.8rem;'>"
    "Diabetes Food Safety Navigator v0.1 — Hackathon MVP<br>"
    "Source: ADA Standards of Care in Diabetes 2026, Section 5<br>"
    "For educational, noncommercial prototype use only."
    "</div>",
    unsafe_allow_html=True,
)
