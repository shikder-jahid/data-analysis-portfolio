"""
Data Cleaning Pipeline — Web App
----------------------------------
A Streamlit interface for the DataCleaner pipeline. Upload a messy CSV/Excel
file, preview it, clean it with one click, and download the cleaned file
plus a change report.

Run locally with:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import io
import tempfile
import os
from clean_pipeline import DataCleaner

st.set_page_config(page_title="Data Cleaning Tool", page_icon="🧹", layout="wide")

st.title("🧹 Automated Data Cleaning Tool")
st.write(
    "Upload a messy CSV or Excel file. This tool will standardize column names, "
    "remove duplicates, handle missing values, fix data types, and give you a "
    "clean file plus a report of everything it changed."
)

with st.sidebar:
    st.header("Settings")
    missing_threshold = st.slider(
        "Drop columns with more than this % missing",
        min_value=10, max_value=90, value=50, step=5,
    ) / 100
    st.caption("Columns missing more data than this threshold get removed entirely.")

uploaded_file = st.file_uploader("Upload your file", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    # Save the upload to a temp path so our existing DataCleaner (built for
    # file paths) can read it without any changes to its logic.
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, uploaded_file.name)
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Preview the raw data
    ext = uploaded_file.name.split(".")[-1].lower()
    raw_df = pd.read_csv(temp_path) if ext == "csv" else pd.read_excel(temp_path)

    st.subheader("📋 Original Data (preview)")
    st.dataframe(raw_df.head(20), use_container_width=True)
    st.caption(f"{raw_df.shape[0]} rows x {raw_df.shape[1]} columns")

    if st.button("🚀 Clean this data", type="primary"):
        output_dir = os.path.join(tempfile.gettempdir(), "cleaned_output")
        cleaner = DataCleaner(temp_path, missing_threshold=missing_threshold, output_dir=output_dir)
        cleaner.log = []  # reset log capture

        with st.spinner("Cleaning in progress..."):
            cleaner.run()

        st.success("Done! Here's what changed:")

        st.subheader("📝 Cleaning Report")
        for line in cleaner.log:
            st.write(f"- {line}")

        st.subheader("✨ Cleaned Data (preview)")
        st.dataframe(cleaner.df.head(20), use_container_width=True)
        st.caption(f"{cleaner.df.shape[0]} rows x {cleaner.df.shape[1]} columns")

        # Prepare downloads
        csv_buffer = io.StringIO()
        cleaner.df.to_csv(csv_buffer, index=False)

        report_text = "DATA CLEANING REPORT\n" + "=" * 50 + "\n"
        report_text += f"Original shape: {cleaner.original_shape[0]} rows x {cleaner.original_shape[1]} columns\n"
        report_text += f"Final shape: {cleaner.df.shape[0]} rows x {cleaner.df.shape[1]} columns\n\n"
        report_text += "STEPS PERFORMED:\n" + "-" * 50 + "\n"
        for line in cleaner.log:
            report_text += f"- {line}\n"

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "⬇️ Download Cleaned CSV",
                data=csv_buffer.getvalue(),
                file_name=f"{uploaded_file.name.rsplit('.', 1)[0]}_cleaned.csv",
                mime="text/csv",
            )
        with col2:
            st.download_button(
                "⬇️ Download Report",
                data=report_text,
                file_name=f"{uploaded_file.name.rsplit('.', 1)[0]}_report.txt",
                mime="text/plain",
            )
else:
    st.info("👆 Upload a file to get started.")
