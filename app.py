import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
import docx
from dotenv import load_dotenv
import json
import time
import plotly.express as px
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

# Load environment variables
load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# -------------- Functions --------------

def get_gemini_response(input_text):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(input_text)
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
    Act as a professional ATS system.
    Analyze the following resume against the provided job description.
    Provide:
    1. JD Match percentage
    2. Missing Keywords (important ones not in resume)
    3. Short Profile Summary

    Output only in this JSON format:
    {{"JD Match":"%","MissingKeywords":[],"Profile Summary":""}}

    Resume:
    {resume_text}

    Job Description:
    {job_description}
    """

def create_improvement_prompt(resume_text, job_description):
    return f"""
    Suggest 5 improvements to boost the following resume for the given job description.
    The suggestions should be actionable and help the candidate improve their chances of matching the job description.

    Resume:
    {resume_text}

    Job Description:
    {job_description}
    """

def generate_pdf_report(result):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width/2, height-50, "Resume Analysis Report")

    c.setFont("Helvetica", 12)
    y = height - 100

    c.drawString(50, y, f"Filename: {result.get('filename', 'N/A')}")
    y -= 30
    c.drawString(50, y, f"JD Match: {result.get('JD Match', '0%')}")
    y -= 30

    missing_keywords = ", ".join(result.get('MissingKeywords', []))
    c.drawString(50, y, "Missing Keywords:")
    y -= 20
    text = c.beginText(70, y)
    text.setFont("Helvetica", 11)
    for keyword in missing_keywords.split(","):
        if keyword.strip():
            text.textLine(f"• {keyword.strip()}")
    c.drawText(text)

    y = text.getY() - 20
    c.drawString(50, y, "Profile Summary:")
    y -= 20
    text = c.beginText(70, y)
    text.setFont("Helvetica", 11)

    summary = result.get('Profile Summary', 'N/A').replace('\n', ' ')
    wrapped = [summary[i:i+90] for i in range(0, len(summary), 90)]
    for line in wrapped:
        text.textLine(line)
    c.drawText(text)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# -------------- Streamlit UI Setup --------------

st.set_page_config(page_title="Smart ATS Ultra 🚀", page_icon="🧠", layout="centered")

# Light/Dark mode toggle
mode = st.sidebar.selectbox("🌗 Choose Theme:", ("Light Mode", "Dark Mode"))

# Custom CSS
if mode == "Light Mode":
    st.markdown("""
    <style>
    body {
        background-color: #f5f7fa;
        color: #333333;
        font-family: 'Poppins', sans-serif;
    }
    .card {
        background: #ffffff;
        padding: 20px;
        border-radius: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        margin-bottom: 30px;
    }
    div.stButton > button {
        border-radius: 12px;
        font-weight: bold;
        font-size: 18px;
        padding: 0.8em 1.2em;
        margin-top: 10px;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    div.stButton > button:has(span:contains("🚀 Start Analysis")) {
        background-color: #1E90FF;
        color: white;
    }
    div.stButton > button:has(span:contains("📤 Upload Resumes")) {
        background-color: #28a745;
        color: white;
    }
    div.stButton > button:has(span:contains("📄 Download")) {
        background-color: #800080;
        color: white;
    }
    div.stButton > button:hover {
        transform: scale(1.05);
    }
    </style>
    """, unsafe_allow_html=True)

else:
    st.markdown("""
    <style>
    body {
        background-color: #1e1e1e;
        color: #ffffff;
        font-family: 'Poppins', sans-serif;
    }
    .card {
        background: #2e2e2e;
        padding: 20px;
        border-radius: 20px;
        box-shadow: 0 4px 12px rgba(255,255,255,0.1);
        margin-bottom: 30px;
    }
    div.stButton > button {
        border-radius: 12px;
        font-weight: bold;
        font-size: 18px;
        padding: 0.8em 1.2em;
        margin-top: 10px;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(255,255,255,0.2);
    }
    div.stButton > button:has(span:contains("🚀 Start Analysis")) {
        background-color: #1E90FF;
        color: white;
    }
    div.stButton > button:has(span:contains("📤 Upload Resumes")) {
        background-color: #28a745;
        color: white;
    }
    div.stButton > button:has(span:contains("📄 Download")) {
        background-color: #800080;
        color: white;
    }
    div.stButton > button:hover {
        transform: scale(1.05);
    }
    </style>
    """, unsafe_allow_html=True)

# -------------- Main App Layout --------------

st.markdown("<h1 style='text-align:center;'>Smart ATS Ultra 🧠🚀</h1>", unsafe_allow_html=True)
st.image("https://www.smartats.io/blog/c29581a3a0c08605647b3cf5845e39bd.png", width=700)
st.markdown("<p style='text-align:center;color:gray;'>Analyze and supercharge your resume easily!</p>", unsafe_allow_html=True)
st.write("---")

# Tabs
upload_tab, results_tab = st.tabs(["📥 Upload & Analyze", "📊 Results"])

if 'batch_results' not in st.session_state:
    st.session_state.batch_results = []

with upload_tab:
    st.header("📚 Upload Resumes & Paste JD")
    jd = st.text_area("Paste Job Description", height=200)
    uploaded_files = st.file_uploader("📤 Upload Resumes (PDF/DOCX)", type=["pdf", "docx"], accept_multiple_files=True)

    if uploaded_files:
        filenames = [f.name for f in uploaded_files]
        st.info(f"📤 Uploaded files: {', '.join(filenames)}")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        analyze = st.button("🚀 Start Analysis", use_container_width=True)

    if analyze:
        if not uploaded_files or not jd:
            st.warning("⚠️ Upload resumes and paste a job description first.")
        else:
            st.session_state.batch_results = []
            progress_bar = st.progress(0.0)
            num_files = len(uploaded_files)
            for i, uploaded_file in enumerate(uploaded_files):
                st.subheader(f"📄 Analyzing: {uploaded_file.name}")
                analysis_placeholder = st.empty()
                with analysis_placeholder:
                    st.info("⚙️ Extracting text...")
                    resume_text = extract_text(uploaded_file)
                    if resume_text:
                        st.info("🧠 Generating analysis...")
                        prompt = create_prompt(resume_text, jd)
                        response = get_gemini_response(prompt)
                        try:
                            result = json.loads(response)
                            result['filename'] = uploaded_file.name
                            improvement_prompt = create_improvement_prompt(resume_text, jd)
                            improvement_response = get_gemini_response(improvement_prompt)
                            result['improvement_suggestions'] = improvement_response
                            st.session_state.batch_results.append(result)
                            st.success(f"✅ Analysis for {uploaded_file.name} completed!")
                        except json.JSONDecodeError:
                            result = {"filename": uploaded_file.name, "raw_response": response}
                            st.session_state.batch_results.append(result)
                            st.error(f"⚠️ Could not parse analysis for {uploaded_file.name}.")
                    else:
                        st.error(f"⚠️ Could not extract text from {uploaded_file.name}.")
                progress_bar.progress((i + 1) / num_files)
            st.success("🎉 Analysis Completed!")
            time.sleep(1)
            st.balloons()
            st.switch_page("pages/Results.py")

with results_tab:
    st.header("📊 Analysis Results")

    if st.session_state.batch_results:
        for result in st.session_state.batch_results:
            st.markdown(f"<div class='card'><h3>📄 {result.get('filename', 'Resume')}</h3>", unsafe_allow_html=True)

            if "raw_response" in result:
                st.warning("Couldn't parse this resume properly.")
                st.write(result["raw_response"])
            else:
                match_percentage = result.get('JD Match', "0").replace('%', '')
                try:
                    match_percentage = float(match_percentage)
                except:
                    match_percentage = 0.0

                badge = "🟢 Excellent" if match_percentage >= 85 else "🟡 Good" if match_percentage >= 60 else "🔴 Needs Improvement"
                st.subheader(f"📊 JD Match: {match_percentage:.1f}% ({badge})")

                fig = px.pie(values=[match_percentage, 100 - match_percentage], names=['Match', 'Gap'], title='Match Overview')
                st.plotly_chart(fig, use_container_width=True)

                missing_keywords = result.get("MissingKeywords", [])
                if missing_keywords:
                    st.subheader("🔹 Missing Keywords")
                    st.write(", ".join(missing_keywords))
                    bar_fig = px.bar(x=missing_keywords, y=[1]*len(missing_keywords), labels={'x':'Keywords','y':'Importance'})
                    st.plotly_chart(bar_fig, use_container_width=True)
                else:
                    st.success("🎉 No missing keywords found!")

                st.subheader("🤐 Profile Summary")
                st.info(result.get('Profile Summary', 'No summary provided.'))

                st.subheader("💡 Suggested Improvements")
                st.info(result.get('improvement_suggestions', 'No suggestions available.'))

                pdf_buffer = generate_pdf_report(result)
                st.download_button(
                    label="📄 Download Individual PDF Report",
                    data=pdf_buffer,
                    file_name=f"{result.get('filename', 'resume')}_report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

            st.markdown("</div>", unsafe_allow_html=True)

        st.download_button(
            label="📦 Download Full Batch Report (JSON)",
            data=json.dumps(st.session_state.batch_results, indent=4),
            file_name="batch_resume_analysis.json",
            mime="application/json",
            use_container_width=True
        )

        csv_data = []
        for result in st.session_state.batch_results:
            if "raw_response" in result:
                continue
            try:
                match = float(result.get('JD Match', '0').replace('%', '').strip())
            except:
                match = 0.0
            csv_data.append({
                "Filename": result.get('filename', ''),
                "JD Match (%)": f"{match:.1f}",
                "Missing Keywords": ", ".join(result.get('MissingKeywords', [])),
                "Profile Summary": result.get('Profile Summary', '').replace('\n', ' ').strip(),
                "Improvement Suggestions": result.get('improvement_suggestions', 'No suggestions')
            })

        if csv_data:
            df = pd.DataFrame(csv_data)
            st.download_button(
                label="📄 Download Batch Report (CSV)",
                data=df.to_csv(index=False),
                file_name="batch_resume_analysis.csv",
                mime="text/csv",
                use_container_width=True
            )

    else:
        st.info("📝 Please upload and analyze resumes first.")

st.markdown("<div style='text-align:center;margin-top:30px;color:gray;'>Made with ❤️ using Streamlit & Gemini 1.5 Flash</div>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;color:gray;'>© 2023 Smart ATS Ultra</div>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;color:gray;'>All rights reserved.</div>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;color:gray;'>Follow us on <a href='https://www.smartats.io'>Smart ATS</a></div>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;color:gray;'>Contact us at <a href='mailto:support@smartats.io'>support@smartats.io</a></div>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;color:gray;'>Privacy Policy | Terms of Service</div>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;color:gray;'>Disclaimer: This tool is for educational purposes only.</div>", unsafe_allow_html=True)
