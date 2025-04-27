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

def get_gemini_response(input):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(input)
    return response.text

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

def create_prompt(resume_text, job_description):
    return f"""
    Act like a skilled ATS (Application Tracking System) expert.
    Evaluate the resume against the job description.
    Provide:
    - JD Match %
    - Missing Keywords
    - Profile Summary

    Resume: {resume_text}
    Job Description: {job_description}

    Respond ONLY in JSON format:
    {{"JD Match":"%","MissingKeywords":[],"Profile Summary":""}}
    """

# Streamlit App Setup
st.set_page_config(page_title="Smart ATS", page_icon="🧠", layout="centered")

# Theme Toggle
theme = st.sidebar.radio("Select Theme:", ("🌞 Light Mode", "🌙 Dark Mode"))

# Apply Animated Background + Neon Text
if theme == "🌙 Dark Mode":
    st.markdown("""
        <style>
        body {
            background: linear-gradient(270deg, #0f2027, #203a43, #2c5364);
            background-size: 800% 800%;
            animation: darkGradient 20s ease infinite;
            color: white;
            font-family: 'Poppins', sans-serif;
        }
        @keyframes darkGradient {
            0% {background-position: 0% 50%;}
            50% {background-position: 100% 50%;}
            100% {background-position: 0% 50%;}
        }
        h1, h3 {
            color: #00FFFF;
            text-shadow: 0 0 10px #00FFFF, 0 0 20px #00FFFF;
        }
        div.stButton > button {
            background: linear-gradient(to right, #8E2DE2, #4A00E0);
            color: white;
            height: 50px;
            border-radius: 12px;
            font-size: 18px;
            transition: 0.3s;
        }
        div.stButton > button:hover {
            transform: scale(1.08);
            background: linear-gradient(to right, #4A00E0, #8E2DE2);
        }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        body {
            background: linear-gradient(270deg, #e0f7fa, #e1bee7, #f0f4c3, #ffe0b2);
            background-size: 800% 800%;
            animation: lightGradient 20s ease infinite;
            color: black;
            font-family: 'Poppins', sans-serif;
        }
        @keyframes lightGradient {
            0% {background-position: 0% 50%;}
            50% {background-position: 100% 50%;}
            100% {background-position: 0% 50%;}
        }
        h1, h3 {
            color: #4CAF50;
            text-shadow: 0 0 5px #4CAF50, 0 0 10px #4CAF50;
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
            transform: scale(1.08);
            background: linear-gradient(to right, #388E3C, #66BB6A);
        }
        </style>
    """, unsafe_allow_html=True)

# App Title
st.markdown("<h1 style='text-align:center;'>Smart ATS 🧠</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;font-size:20px;'>Boost your chances! Match your resume with job descriptions.</p>", unsafe_allow_html=True)
st.write("---")

# Session State
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False
    st.session_state.result_data = {}

# Tabs
tab1, tab2 = st.tabs(["📥 Upload & Input", "📊 Results"])

with tab1:
    st.header("📄 Paste Job Description & Upload Resume")
    jd = st.text_area("Job Description", height=200, placeholder="Paste the Job Description here...")
    uploaded_file = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf", "docx"], help="Only PDF or DOCX files supported.")

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        submit = st.button("🚀 Analyze Resume", use_container_width=True)

    if submit:
        if uploaded_file is not None and jd:
            with st.spinner("Analyzing your resume... Please wait ⏳"):
                resume_text = extract_text(uploaded_file)
                if resume_text is None:
                    st.error("Unsupported file format.")
                else:
                    prompt = create_prompt(resume_text, jd)
                    response = get_gemini_response(prompt)

                    try:
                        result = json.loads(response)
                        st.session_state.result_data = result
                        st.session_state.analysis_done = True
                        st.success("✅ Resume analysis completed! Go to 'Results' tab.")
                        time.sleep(1)
                        st.balloons()
                    except:
                        st.session_state.result_data = {"raw_response": response}
                        st.session_state.analysis_done = True
                        st.warning("⚠️ Couldn't parse properly. Showing raw output.")
        else:
            st.warning("⚠️ Please upload a resume and paste the Job Description.")

with tab2:
    st.header("📊 Your Analysis Results")

    if st.session_state.analysis_done:
        result = st.session_state.result_data

        if "raw_response" in result:
            st.warning("⚠️ Raw Response:")
            st.write(result["raw_response"])
        else:
            match_percentage = result.get('JD Match', "0").replace('%', '')
            try:
                match_percentage = float(match_percentage)
            except:
                match_percentage = 0.0

            st.markdown(f"""
                <div style="padding:20px;border-radius:10px;background:rgba(255,255,255,0.1);">
                    <h3>📈 JD Match</h3>
                    <h1 style="text-align:center;">{match_percentage:.1f}%</h1>
                </div>
            """, unsafe_allow_html=True)

            st.progress(int(match_percentage))

            missing_keywords = result.get("MissingKeywords", [])
            st.markdown("<div style='padding:20px;border-radius:10px;background:rgba(255,255,255,0.1);'><h3>🧩 Missing Keywords</h3>", unsafe_allow_html=True)
            if missing_keywords:
                st.write(", ".join(missing_keywords))
            else:
                st.write("No missing keywords! Excellent profile! 👏")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown(f"""
                <div style="padding:20px;border-radius:10px;background:rgba(255,255,255,0.1);">
                    <h3>🧠 Profile Summary</h3>
                    <p>{result.get('Profile Summary', 'No summary provided.')}</p>
                </div>
            """, unsafe_allow_html=True)

            st.download_button(
                label="📥 Download Analysis Report (JSON)",
                data=json.dumps(result, indent=4),
                file_name="resume_analysis_report.json",
                mime="application/json",
                use_container_width=True
            )

    else:
        st.info("📥 Please upload and analyze your resume first in 'Upload & Input' tab.")

# Footer
st.markdown("<div style='text-align:center;color:gray;margin-top:30px;'>Made with ❤️ using Streamlit and Gemini 1.5</div>", unsafe_allow_html=True)
