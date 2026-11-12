import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
import pandas as pd
from backend.claim_service import process_document
from backend.database import list_claims, get_claim, delete_claim

st.set_page_config(page_title="AI Insurance Claims Automation", page_icon="📄", layout="wide")
st.title("AI Insurance Claims Processing Automation")
st.caption("Document extraction and reviewer assistance — every claim requires human verification.")

with st.sidebar:
    st.header("Processing settings")
    use_ai = st.checkbox("Use Gemini AI summary (if API key configured)", value=True)
    st.info("Without a Gemini key, the app uses a local rule-based summary. SQLite is used by default; MongoDB is optional.")

tab_upload, tab_records, tab_about = st.tabs(["Upload & Process", "Claim Records", "About"])

with tab_upload:
    st.subheader("Upload an insurance claim document")
    uploaded = st.file_uploader("Choose PDF or image", type=["pdf", "png", "jpg", "jpeg", "tif", "tiff"])
    if uploaded:
        st.write(f"**File:** {uploaded.name} · **Size:** {uploaded.size:,} bytes")
        if st.button("Process document", type="primary"):
            with st.spinner("Extracting and validating document..."):
                try:
                    claim = process_document(uploaded.name, uploaded.getvalue(), use_ai=use_ai)
                    st.session_state["last_claim_id"] = claim["claim_id"]
                    st.success("Document processed and saved for human review.")
                except Exception as exc:
                    st.error(f"Processing failed: {exc}")

    claim_id = st.session_state.get("last_claim_id")
    if claim_id:
        claim = get_claim(claim_id)
        if claim:
            st.divider()
            st.subheader("Extracted claim information")
            c1, c2, c3 = st.columns(3)
            c1.metric("Claim status", claim["status"])
            c2.metric("Claim amount", f"{claim['claim_amount']:,.2f}" if claim["claim_amount"] is not None else "Not found")
            c3.metric("Validation flags", len(claim["flags"]))
            fields = ["patient_name", "policy_number", "hospital_name", "claim_date", "diagnosis"]
            left, right = st.columns(2)
            for idx, field in enumerate(fields):
                (left if idx % 2 == 0 else right).write(
                    f"**{field.replace('_', ' ').title()}:** {claim.get(field) or 'Not found'}"
                )
            st.markdown("**AI / Rule-based summary**")
            st.write(claim["summary"])
            if claim["flags"]:
                st.warning("Manual review flags")
                for flag in claim["flags"]:
                    st.write(f"- {flag}")
            else:
                st.info("No configured validation flags. Human verification is still required.")
            with st.expander("View extracted source text"):
                st.text(claim["extracted_text"] or "No text extracted.")

with tab_records:
    st.subheader("Saved claim records")
    records = list_claims()
    if records:
        display = pd.DataFrame(records)
        columns = ["claim_id", "patient_name", "policy_number", "hospital_name", "claim_amount", "claim_date", "status", "source_filename"]
        st.dataframe(display[columns], use_container_width=True, hide_index=True)
        selected = st.selectbox("Select claim ID for details", [r["claim_id"] for r in records])
        selected_claim = get_claim(selected)
        if selected_claim:
            st.write(selected_claim["summary"])
            st.write("Validation flags:", selected_claim["flags"])
            if st.button("Delete selected record"):
                delete_claim(selected)
                st.rerun()
        csv = display.to_csv(index=False).encode("utf-8")
        st.download_button("Download records as CSV", csv, "claims_export.csv", "text/csv")
    else:
        st.info("No claims processed yet.")

with tab_about:
    st.subheader("System capabilities")
    st.markdown("""
    - PDF text extraction and OCR fallback for scanned PDFs and images.
    - Rule-based field extraction and required-field validation.
    - Optional Gemini 2.5 Flash summary generation.
    - Local SQLite persistence with optional MongoDB mirroring.
    - FastAPI endpoints for integration with other applications.
    - CSV export for reporting.

    **Important:** This prototype does not determine medical necessity, coverage,
    fraud, approval, or rejection. It is not connected to insurer or hospital portals.
    A qualified human reviewer must verify all extracted information.
    """)
