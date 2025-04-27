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

# Load environment variables
load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

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

# Streamlit Config
st.set_page_config(page_title="Smart ATS", page_icon="🧠", layout="centered")

# Theme Toggle
theme = st.sidebar.selectbox("🌗 Select Theme", ["Light", "Dark"])
primaryColor = "#4CAF50" if theme == "Light" else "#90CAF9"
backgroundColor = "#ffffff" if theme == "Light" else "#0e1117"
textColor = "#000000" if theme == "Light" else "#ffffff"

# Custom CSS
st.markdown(f"""
<style>
body {{
    background: {backgroundColor};
    color: {textColor};
    font-family: 'Poppins', sans-serif;
}}
h1 {{
    color: {primaryColor};
    text-align: center;
}}
.card {{
    background: #ffffff10;
    padding: 20px;
    border-radius: 15px;
    margin-bottom: 20px;
}}
.footer {{
    text-align: center;
    font-size: 14px;
    margin-top: 50px;
    color: {textColor};
}}
</style>
""", unsafe_allow_html=True)

# Title
st.markdown("<h1>Smart ATS 🧠</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align:center;color:{textColor};'>Analyze and Boost your Resume against Job Descriptions!</p>", unsafe_allow_html=True)
st.write("---")

# Tabs
upload_tab, results_tab = st.tabs(["📥 Upload & Analyze", "📊 Results"])

if 'batch_results' not in st.session_state:
    st.session_state.batch_results = []

with upload_tab:
    st.header("📚 Upload Resumes & Paste JD")
    jd = st.text_area("Paste Job Description", height=200)
    uploaded_files = st.file_uploader("Upload one or multiple resumes (PDF/DOCX)", type=["pdf", "docx"], accept_multiple_files=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        analyze = st.button("🚀 Start Analysis", use_container_width=True)

    if analyze:
        if not uploaded_files or not jd:
            st.warning("⚠️ Upload at least one resume and paste JD.")
        else:
            st.session_state.batch_results = []
            with st.spinner("Analyzing resumes..."):
                for uploaded_file in uploaded_files:
                    resume_text = extract_text(uploaded_file)
                    if resume_text:
                        prompt = create_prompt(resume_text, jd)
                        response = get_gemini_response(prompt)
                        try:
                            result = json.loads(response)
                            result['filename'] = uploaded_file.name
                        except:
                            result = {"filename": uploaded_file.name, "raw_response": response}
                        st.session_state.batch_results.append(result)
                st.success("✅ Analysis Completed!")
                time.sleep(1)
                st.balloons()

with results_tab:
    st.header("📊 Analysis Results")

    if st.session_state.batch_results:
        for result in st.session_state.batch_results:
            st.markdown(f"""
            <div class='card'>
            <h3>{'📚' + result.get('filename', 'Resume')}</h3>
            """, unsafe_allow_html=True)

            if "raw_response" in result:
                st.warning("Couldn't parse this resume properly.")
                st.write(result["raw_response"])
            else:
                # JD Match
                match_percentage = result.get('JD Match', "0").replace('%', '')
                try:
                    match_percentage = float(match_percentage)
                except:
                    match_percentage = 0.0

                if match_percentage >= 85:
                    badge = "🟢 Excellent"
                elif match_percentage >= 60:
                    badge = "🟡 Good"
                else:
                    badge = "🔴 Needs Improvement"

                st.subheader(f"📊 JD Match: {match_percentage:.1f}% ({badge})")
                fig = px.pie(values=[match_percentage, 100-match_percentage], names=['Match', 'Gap'], title='Match Overview')
                st.plotly_chart(fig, use_container_width=True)

                # Missing Keywords
                missing_keywords = result.get("MissingKeywords", [])
                if missing_keywords:
                    st.subheader("🔹 Missing Keywords")
                    st.write(", ".join(missing_keywords))
                    bar_fig = px.bar(x=missing_keywords, y=[1]*len(missing_keywords), labels={'x':'Keywords','y':'Importance'})
                    st.plotly_chart(bar_fig, use_container_width=True)
                else:
                    st.success("🎉 No missing keywords! Perfect Match!")

                # Profile Summary
                st.subheader("🤐 Profile Summary")
                st.info(result.get('Profile Summary', 'No summary provided.'))

            st.markdown("</div>", unsafe_allow_html=True)

        # --- Download Buttons Section ---

        # Download JSON
        st.download_button(
            label="📦 Download Full Batch Report (JSON)",
            data=json.dumps(st.session_state.batch_results, indent=4),
            file_name="batch_resume_analysis.json",
            mime="application/json",
            use_container_width=True
        )

        # Download Clean CSV
        csv_data = []
        for result in st.session_state.batch_results:
            if "raw_response" in result:
                continue  # Skip unstructured responses
            try:
                match = float(result.get('JD Match', '0').replace('%', '').strip())
            except:
                match = 0.0

            csv_data.append({
                "Filename": result.get('filename', ''),
                "JD Match (%)": f"{match:.1f}",
                "Missing Keywords": ", ".join(result.get('MissingKeywords', [])),
                "Profile Summary": result.get('Profile Summary', '').replace('\n', ' ').strip()
            })

        if csv_data:
            df = pd.DataFrame(csv_data)
            df = df[["Filename", "JD Match (%)", "Missing Keywords", "Profile Summary"]]
            st.download_button(
                label="📄 Download Batch Report (CSV)",
                data=df.to_csv(index=False),
                file_name="batch_resume_analysis.csv",
                mime="text/csv",
                use_container_width=True
            )

    else:
        st.info("📝 Please upload and analyze resumes first.")

# Footer
st.markdown("<div style='text-align:center;color:gray;margin-top:30px;'>Made with ❤️ using Streamlit and Gemini 1.5</div>", unsafe_allow_html=True)

