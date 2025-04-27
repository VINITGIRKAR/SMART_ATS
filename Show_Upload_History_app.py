import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
import docx
from dotenv import load_dotenv
import json
import time

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

# Set page config
st.set_page_config(page_title="Smart ATS Ultra Pro 🚀", page_icon="🧠", layout="centered")

# Session State for Theme
if "theme" not in st.session_state:
    st.session_state.theme = "light"

# Theme Toggle Button
with st.sidebar:
    st.title("🌗 Theme Settings")
    theme_toggle = st.toggle("Dark Mode", value=st.session_state.theme=="dark")
    st.divider()

    if theme_toggle:
        st.session_state.theme = "dark"
    else:
        st.session_state.theme = "light"

# Custom CSS
if st.session_state.theme == "dark":
    st.markdown("""
        <style>
        body {
            background: linear-gradient(135deg, #1e1e2f, #12121f);
            color: #f5f5f5;
            font-family: 'Poppins', sans-serif;
        }
        h1, h3 {
            color: #00ffea;
            text-shadow: 0 0 10px #00ffea;
        }
        .card {
            background: #2c2c3c;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 0 20px rgba(0,255,234,0.2);
            animation: fadeIn 1s ease-in-out;
            margin-bottom: 20px;
        }
        div.stButton > button {
            background: linear-gradient(90deg, #00ffea, #0066ff);
            color: black;
            height: 50px;
            border-radius: 12px;
            font-size: 18px;
            transition: 0.3s;
        }
        div.stButton > button:hover {
            background: linear-gradient(90deg, #0066ff, #00ffea);
            transform: scale(1.05);
        }
        .footer {
            text-align: center;
            font-size: 14px;
            color: #888;
            margin-top: 50px;
        }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        body {
            background: linear-gradient(135deg, #e0f7fa, #e1bee7);
            font-family: 'Poppins', sans-serif;
        }
        h1, h3 {
            color: #4CAF50;
        }
        .card {
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            animation: fadeIn 1s ease-in-out;
            margin-bottom: 20px;
        }
        div.stButton > button {
            background: linear-gradient(to right, #4CAF50, #81C784);
            color: white;
            height: 50px;
            border-radius: 12px;
            font-size: 18px;
            transition: 0.3s;
        }
        div.stButton > button:hover {
            background: linear-gradient(to right, #388E3C, #66BB6A);
            transform: scale(1.05);
        }
        .footer {
            text-align: center;
            font-size: 14px;
            color: #555;
            margin-top: 50px;
        }
        </style>
    """, unsafe_allow_html=True)

# Title
st.markdown("<h1>Smart ATS Ultra Pro 🧠</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>Upload your Resume, Paste JD, Get Instant ATS Analysis 📈</p>", unsafe_allow_html=True)
st.write("---")

# Session State for analysis
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
    st.session_state.result_data = {}
    st.session_state.history = []

# Tabs
tab1, tab2 = st.tabs(["📥 Upload & Input", "📊 Results"])

with tab1:
    st.header("📄 Upload Resume & Paste Job Description")
    jd = st.text_area("Paste Job Description Here", height=200)
    uploaded_file = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf", "docx"])

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        submit = st.button("🚀 Analyze Resume", use_container_width=True)

    if submit:
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
                            "match": result.get("JD Match", "0%")
                        })
                        st.success("✅ Resume analysis completed! Go to 'Results' tab.")
                        time.sleep(1)
                        st.balloons()
                    except:
                        st.warning("⚠️ Couldn't parse the response properly.")
                        st.session_state.result_data = {"raw_response": response}
                        st.session_state.analysis_done = True
        else:
            st.warning("⚠️ Please upload a resume and paste the JD.")

with tab2:
    st.header("📊 Analysis Results")
    if st.session_state.analysis_done:
        result = st.session_state.result_data
        if "raw_response" in result:
            st.warning("⚠️ Showing raw response:")
            st.code(result["raw_response"])
        else:
            # JD Match %
            match_percentage = result.get("JD Match", "0").replace("%", "")
            try:
                match_percentage = float(match_percentage)
            except:
                match_percentage = 0.0

            match_color = "#4CAF50"  # Green
            if match_percentage < 50:
                match_color = "#ff1744"  # Red
            elif match_percentage < 75:
                match_color = "#ffc400"  # Yellow

            st.markdown(f"""
                <div class="card">
                    <h3>📈 JD Match Percentage</h3>
                    <h1 style="color:{match_color};">{match_percentage:.1f}%</h1>
                </div>
            """, unsafe_allow_html=True)
            st.progress(int(match_percentage))

            # Missing Keywords
            st.markdown("""<div class="card"><h3>🧩 Missing Keywords</h3>""", unsafe_allow_html=True)
            missing_keywords = result.get("MissingKeywords", [])
            if missing_keywords:
                st.write(", ".join(missing_keywords))
            else:
                st.success("No missing keywords found! 💪")
            st.markdown("</div>", unsafe_allow_html=True)

            # Profile Summary
            st.markdown(f"""
                <div class="card">
                    <h3>🧠 Profile Summary</h3>
                    <p>{result.get('Profile Summary', 'No summary provided.')}</p>
                </div>
            """, unsafe_allow_html=True)

            # Download Button
            st.download_button(
                label="📥 Download Report (JSON)",
                data=json.dumps(result, indent=4),
                file_name="resume_analysis_report.json",
                mime="application/json",
                use_container_width=True
            )

        # Show Upload History
        st.markdown("<br><h3>📂 Previous Uploads</h3>", unsafe_allow_html=True)
        for item in st.session_state.history[::-1]:
            st.write(f"• {item['file_name']} - Match: {item['match']}")

    else:
        st.info("Upload your resume and paste JD first to see the results.")

# Footer
st.markdown("<div class='footer'>Made with ❤️ using Streamlit and Gemini 1.5 Flash | Ultra Pro Version 🚀</div>", unsafe_allow_html=True)
