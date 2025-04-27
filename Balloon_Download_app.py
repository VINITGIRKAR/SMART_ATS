import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
import docx
from dotenv import load_dotenv
import json
import time
from io import BytesIO
import zipfile

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to get response from Gemini
def get_gemini_response(input):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(input)
    return response.text

# Function to extract text from PDF or DOCX
def extract_text(uploaded_file):
    if uploaded_file.name.endswith('.pdf'):
        reader = pdf.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    elif uploaded_file.name.endswith('.docx'):
        doc = docx.Document(uploaded_file)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    else:
        return None

# Create prompt for Gemini
def create_prompt(resume_text, job_description):
    return f"""
    Act like a professional ATS (Application Tracking System) specialized in tech roles like software engineering, data science, analytics, and big data.
    Evaluate the following resume against the job description. Be very strict and accurate.

    Resume: {resume_text}

    Job Description: {job_description}

    Respond in one string as:
    {{"JD Match":"%","MissingKeywords":[],"Profile Summary":""}}
    """

# Streamlit Page Config
st.set_page_config(page_title="Smart ATS Ultra Pro 🚀", page_icon="🧠", layout="centered")

# Session State Defaults
if "theme" not in st.session_state:
    st.session_state.theme = "light"
if "fun_mode" not in st.session_state:
    st.session_state.fun_mode = False
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
    st.session_state.result_data = {}
    st.session_state.history = []

# Sidebar Theme & Fun Mode
with st.sidebar:
    st.title("⚙️ Settings")
    theme_toggle = st.toggle("Dark Mode", value=st.session_state.theme == "dark")
    fun_mode_toggle = st.toggle("🎈 Fun Mode (Balloons)", value=st.session_state.fun_mode)
    st.session_state.theme = "dark" if theme_toggle else "light"
    st.session_state.fun_mode = fun_mode_toggle
    st.divider()

# Custom CSS & Backgrounds
if st.session_state.theme == "dark":
    bg_css = """
        <style>
        body {
            background: linear-gradient(135deg, #1e1e2f, #12121f);
            color: #f5f5f5;
            font-family: 'Poppins', sans-serif;
        }
        """
else:
    bg_css = """
        <style>
        body {
            background: linear-gradient(135deg, #e0f7fa, #e1bee7);
            font-family: 'Poppins', sans-serif;
        }
        """

# 🎈 Fun Mode Background (Floating Balloons)
if st.session_state.fun_mode:
    bg_css += """
    body::before {
        content: "";
        background: url('https://cdn.pixabay.com/animation/2023/03/14/15/57/15-57-33-298_512.gif') repeat;
        opacity: 0.2;
        position: fixed;
        top: 0; left: 0;
        height: 100%; width: 100%;
        z-index: -1;
    }
    """

bg_css += """
    h1, h3 {
        color: #00ffea;
    }
    .card {
        background: #2c2c3c;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 0 20px rgba(0,255,234,0.2);
        margin-bottom: 20px;
    }
    div.stButton > button {
        background: linear-gradient(90deg, #00ffea, #0066ff);
        color: black;
        border-radius: 12px;
        font-size: 18px;
        height: 50px;
    }
    div.stButton > button:hover {
        transform: scale(1.05);
    }
    .footer {
        text-align: center;
        font-size: 14px;
        color: #888;
        margin-top: 50px;
    }
    </style>
    """
st.markdown(bg_css, unsafe_allow_html=True)

# Title
st.markdown("<h1 style='text-align:center;'>Smart ATS Ultra Pro 🧠</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>Upload your Resume, Paste JD, Get Instant ATS Analysis 📈</p>", unsafe_allow_html=True)
st.write("---")

# Tabs
tab1, tab2 = st.tabs(["📥 Upload & Input", "📊 Results"])

with tab1:
    st.header("📄 Upload Resume & Paste Job Description")
    jd = st.text_area("Paste Job Description Here", height=200)
    uploaded_file = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf", "docx"])

    if st.button("🚀 Analyze Resume", use_container_width=True):
        if uploaded_file and jd:
            with st.spinner("Analyzing your resume... Hang tight! ⏳"):
                resume_text = extract_text(uploaded_file)
                if resume_text:
                    prompt = create_prompt(resume_text, jd)
                    response = get_gemini_response(prompt)
                    try:
                        result = json.loads(response)
                        st.session_state.result_data = result
                        st.session_state.analysis_done = True
                        st.session_state.history.append({
                            "file_name": uploaded_file.name,
                            "match": result.get("JD Match", "0%"),
                            "report": result
                        })
                        st.success("✅ Analysis Complete!")
                        if st.session_state.fun_mode:
                            st.balloons()
                        time.sleep(1)
                    except:
                        st.warning("⚠️ Couldn't parse Gemini response.")
                        st.session_state.result_data = {"raw_response": response}
                        st.session_state.analysis_done = True
        else:
            st.warning("⚠️ Upload your resume and paste a job description.")

with tab2:
    st.header("📊 Analysis Results")
    if st.session_state.analysis_done:
        result = st.session_state.result_data
        if "raw_response" in result:
            st.warning("⚠️ Raw Gemini response shown below:")
            st.code(result["raw_response"])
        else:
            match_percentage = result.get("JD Match", "0").replace("%", "")
            try:
                match_percentage = float(match_percentage)
            except:
                match_percentage = 0.0

            color = "#4CAF50" if match_percentage >= 75 else "#ffc400" if match_percentage >= 50 else "#ff1744"
            st.markdown(f"""
                <div class="card">
                    <h3>📈 JD Match Percentage</h3>
                    <h1 style="color:{color};">{match_percentage:.1f}%</h1>
                </div>
            """, unsafe_allow_html=True)
            st.progress(int(match_percentage))

            st.markdown("""<div class="card"><h3>🧩 Missing Keywords</h3>""", unsafe_allow_html=True)
            missing_keywords = result.get("MissingKeywords", [])
            if missing_keywords:
                st.write(", ".join(missing_keywords))
            else:
                st.success("No missing keywords! 🎯")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown(f"""
                <div class="card">
                    <h3>🧠 Profile Summary</h3>
                    <p>{result.get('Profile Summary', 'No summary provided.')}</p>
                </div>
            """, unsafe_allow_html=True)

            st.download_button(
                label="📥 Download Report (JSON)",
                data=json.dumps(result, indent=4),
                file_name="resume_analysis_report.json",
                mime="application/json",
                use_container_width=True
            )

        # Batch Download
        if st.session_state.history:
            def create_zip():
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                    for i, item in enumerate(st.session_state.history):
                        filename = f"{i+1}_{item['file_name'].replace(' ', '_')}_report.json"
                        zip_file.writestr(filename, json.dumps(item["report"], indent=4))
                zip_buffer.seek(0)
                return zip_buffer

            st.download_button(
                label="🧳 Download All Reports (ZIP)",
                data=create_zip(),
                file_name="all_resume_reports.zip",
                mime="application/zip",
                use_container_width=True
            )

        st.markdown("<h3>📂 Upload History</h3>", unsafe_allow_html=True)
        for item in st.session_state.history[::-1]:
            st.write(f"• {item['file_name']} - Match: {item['match']}")
    else:
        st.info("📎 Upload and analyze a resume to see results here.")

# Footer
st.markdown("<div class='footer'>Made with ❤️ using Streamlit and Gemini 1.5 Flash | Ultra Pro Version 🚀</div>", unsafe_allow_html=True)
