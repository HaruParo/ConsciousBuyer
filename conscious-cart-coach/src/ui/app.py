"""
Streamlit UI application.
Main entry point for the Conscious Cart Coach web interface.
"""

import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    st.set_page_config(
        page_title="Conscious Cart Coach",
        page_icon="🛒",
        layout="wide"
    )

    st.title("🛒 Conscious Cart Coach")
    st.markdown("*Make more conscious purchasing decisions*")

    # Sidebar
    with st.sidebar:
        st.header("Settings")
        # Add settings here

    # Main content
    st.header("Upload Your Receipts")
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

    if uploaded_file is not None:
        st.success("File uploaded successfully!")
        # Process file here

    st.header("Your Recommendations")
    st.info("Upload receipts to get personalized recommendations.")


if __name__ == "__main__":
    main()
