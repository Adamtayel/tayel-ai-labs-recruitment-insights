import streamlit as st
import asyncio
from main2 import run_agent, create_pdf

# Page configuration
st.set_page_config(
    page_title="Tayel AI Analyzer",
    page_icon="",
    layout="centered"
)

# Custom UI styling
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.stApp {
    background-color: #0e1117;
}

.main-title {
    color: #FFFFFF;
    font-family: 'Inter', sans-serif;
    font-weight: 800;
    text-align: center;
    font-size: 42px;
    margin-bottom: 10px;
    background: -webkit-linear-gradient(#00c6ff, #0072ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.report-box {
    padding: 25px;
    border-radius: 15px;
    background-color: #161b22;
    border: 1px solid #30363d;
    color: #c9d1d9;
    line-height: 1.6;
    font-size: 16px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
}

.stButton>button {
    background: linear-gradient(45deg, #0072ff, #00c6ff);
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 12px;
    font-weight: bold;
    transition: 0.3s;
}

.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(0,114,255,0.4);
}
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="main-title">Tayel AI Analyzer</h1>', unsafe_allow_html=True)

# Input section
url = st.text_input("LinkedIn Profile URL", placeholder="https://www.linkedin.com/in/username")

col1, col2 = st.columns(2)

with col1:
    lang = st.segmented_control("Language", ["Arabic", "English"], default="Arabic")

with col2:
    mode = st.segmented_control("Analysis Depth", ["Standard", "Deep"], default="Standard")

lang_code = '1' if lang == "Arabic" else '2'

if st.button("Run Intelligence Analysis"):
    if not url:
        st.warning("Please provide a valid LinkedIn URL.")
    else:
        with st.spinner("Processing..."):
            result = asyncio.run(run_agent(url, lang_code))

            if "Error" in result:
                st.error(result)
            else:
                st.markdown("Analysis Result")
                st.markdown(f'<div class="report-box">{result}</div>', unsafe_allow_html=True)

                pdf_file = create_pdf(result, lang_code)
                with open(pdf_file, "rb") as f:
                    st.download_button(
                        label="Export to PDF",
                        data=f,
                        file_name=pdf_file,
                        mime="application/pdf"
                    )

st.markdown("<p style='text-align: center; color: #8b949e;'>Engineered by Tayel AI Labs</p>", unsafe_allow_html=True)
