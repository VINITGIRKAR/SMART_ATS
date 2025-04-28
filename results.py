import streamlit as st
import plotly.express as px
import json
import pandas as pd

# -------------- Main Layout --------------
st.set_page_config(page_title="Smart ATS Results", page_icon="📊", layout="centered")

# Display title and subheading
st.title("📊 Analysis Results")
st.write("This page displays the analysis results for each uploaded resume.")

# Check if analysis results exist in session_state
if 'batch_results' not in st.session_state or not st.session_state.batch_results:
    st.info("No analysis results available. Please upload and analyze resumes first.")
else:
    # Loop through all the results and display them
    for result in st.session_state.batch_results:
        st.markdown(f"<div class='card'><h3>📄 {result.get('filename', 'Resume')}</h3>", unsafe_allow_html=True)

        # Parse the raw JSON response
        raw_response = result.get('raw_response', '')
        try:
            analysis_result = json.loads(raw_response.strip('```json\n').strip())
        except Exception as e:
            st.error(f"Error parsing JSON: {e}")
            continue

        # Display JD Match with a pie chart
        match_percentage = analysis_result.get('JD Match', "0").replace('%', '')
        try:
            match_percentage = float(match_percentage)
        except:
            match_percentage = 0.0

        badge = "🟢 Excellent" if match_percentage >= 85 else "🟡 Good" if match_percentage >= 60 else "🔴 Needs Improvement"
        st.subheader(f"📊 JD Match: {match_percentage:.1f}% ({badge})")

        # Pie chart of JD match
        fig = px.pie(values=[match_percentage, 100 - match_percentage], names=['Match', 'Gap'], title='Match Overview')
        st.plotly_chart(fig, use_container_width=True)

        # Display Missing Keywords
        missing_keywords = analysis_result.get("MissingKeywords", [])
        if missing_keywords:
            st.subheader("🔹 Missing Keywords")
            st.write(", ".join(missing_keywords))
            # Create bar chart for missing keywords
            bar_fig = px.bar(x=missing_keywords, y=[1]*len(missing_keywords), labels={'x':'Keywords','y':'Importance'})
            st.plotly_chart(bar_fig, use_container_width=True)
        else:
            st.success("🎉 No missing keywords found!")

        # Display Profile Summary
        st.subheader("🤐 Profile Summary")
        st.info(analysis_result.get('Profile Summary', 'No summary provided.'))

        # Display Improvement Suggestions (if available)
        improvement_suggestions = result.get('improvement_suggestions', '')
        if improvement_suggestions:
            st.subheader("💡 Suggested Improvements")
            st.info(improvement_suggestions)
        else:
            st.info("No suggestions available.")

        # Allow users to download individual PDF reports
        st.download_button(
            label="📄 Download Individual PDF Report",
            data=result.get('filename', 'resume') + "_report.pdf",  # Placeholder for the actual report generation logic
            file_name=f"{result.get('filename', 'resume')}_report.pdf",
            mime="application/pdf",
            use_container_width=True
        )

        st.markdown("</div>", unsafe_allow_html=True)

    # Batch Report download options
    st.download_button(
        label="📦 Download Full Batch Report (JSON)",
        data=json.dumps(st.session_state.batch_results, indent=4),
        file_name="batch_resume_analysis.json",
        mime="application/json",
        use_container_width=True
    )

    # Create and allow downloading a CSV report
    csv_data = []
    for result in st.session_state.batch_results:
        # Parse the raw JSON response
        raw_response = result.get('raw_response', '')
        try:
            analysis_result = json.loads(raw_response.strip('```json\n').strip())
        except Exception as e:
            st.error(f"Error parsing JSON: {e}")
            continue

        try:
            match = float(analysis_result.get('JD Match', '0').replace('%', '').strip())
        except:
            match = 0.0
        csv_data.append({
            "Filename": result.get('filename', ''),
            "JD Match (%)": f"{match:.1f}",
            "Missing Keywords": ", ".join(analysis_result.get('MissingKeywords', [])),
            "Profile Summary": analysis_result.get('Profile Summary', '').replace('\n', ' ').strip(),
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

# Footer Section
st.markdown("<div style='text-align:center;margin-top:30px;color:gray;'>Made with ❤️ using Streamlit & Gemini 1.5 Flash</div>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;color:gray;'>© 2023 Smart ATS Ultra</div>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;color:gray;'>All rights reserved.</div>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;color:gray;'>Follow us on <a href='https://www.smartats.io'>Smart ATS</a></div>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;color:gray;'>Contact us at <a href='mailto:support@smartats.io'>support@smartats.io</a></div>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;color:gray;'>Privacy Policy | Terms of Service</div>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;color:gray;'>Disclaimer: This tool is for educational purposes only.</div>", unsafe_allow_html=True)
