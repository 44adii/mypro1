# app.py

import streamlit as st
from dotenv import load_dotenv

# Load environment BEFORE importing anything that constructs LLMs
load_dotenv()

# Imports moved to lazy loading functions to speed up app startup
# from crew import legal_assistant_crew
# from tools.email_tool import send_email_smtp

st.set_page_config(page_title="AI Legal Assistant", page_icon="🧠", layout="wide")

st.title("⚖️ Personal AI Legal Assistant")
st.markdown(
    "Enter a legal problem in plain English or Hindi. This assistant will help you:\n"
    "- Understand the legal issue\n"
    "- Find applicable IPC sections\n"
    "- Retrieve matching precedent cases\n"
    "- Generate a formal legal document"
)

@st.cache_resource
def load_crew():
    """Lazy load the crew to avoid app startup delay."""
    from crew import legal_assistant_crew
    return legal_assistant_crew

    

# --- Voice Input Section ---
st.markdown("### 🎙️ Voice Input")
from audio_recorder_streamlit import audio_recorder
import google.generativeai as genai
import os

audio_bytes = audio_recorder( text="", recording_color="#e8b62c", neutral_color="#6aa36f", icon_name="microphone", icon_size="2x")

transcribed_text = ""
if audio_bytes:
    # Check if we already transcribed this exact audio to avoid re-running on every slight interaction
    # For simplicity, we just run it. Using session state would be better for distinct recordings.
    st.info("🎧 Transcribing audio...")
    try:
        # Configure GenAI with the API Key
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel("gemini-2.5-flash-lite")
        
        # Generate content from audio bytes
        response = model.generate_content([
            "Transcribe the following legal issue description exactly into English or Hindi as spoken.",
            {"mime_type": "audio/mp3", "data": audio_bytes}
        ])
        transcribed_text = response.text
        st.success("✅ Transcription Complete!")
    except Exception as e:
        st.error(f"❌ Transcription failed: {e}")

# Use transcribed text if available, otherwise use previous input
default_input = transcribed_text if transcribed_text else ""

submitted = False
with st.form("legal_form"):
    col1, col2 = st.columns([3, 1])
    with col1:
        # If we have transcribed text, we value=transcribed_text. 
        # Note: This might reset if user types manually then records again. 
        user_input = st.text_area("📝 Describe your legal issue (Type or Speak):", value=default_input, height=250)
    with col2:
        language_pref = st.selectbox(
            "🌐 Response Language",
            options=["english", "hindi", "both"],
            index=0,
            help="Choose your preferred language for the legal response"
        )
        lawyer_email = st.text_input(
            "📧 Lawyer Email (optional)",
            help="Provide a nearby lawyer's email to send the final document"
        )
        send_lawyer_email = st.checkbox("Send final document to lawyer", value=False)
    
    submitted = st.form_submit_button("🔍 Run Legal Assistant")

if submitted:
    if not user_input.strip():
        st.warning("Please enter a legal issue to analyze.")
    else:
        with st.spinner("🔎 Analyzing your case and preparing legal output..."):
            legal_crew = load_crew()
            
            from utils.retry_handler import execute_crew_with_retry
            
            try:
                result = execute_crew_with_retry(legal_crew, inputs={
                    "user_input": user_input,
                    "language_preference": language_pref
                })
            except Exception as e:
                st.error(f"❌ Execution failed: {e}")
                st.stop()


        st.success("✅ Legal Assistant completed the workflow!")

        # --- NEW: Display Advisory Agent Output (Task 1) ---
        import json
        try:
            # Task 0: Intake, Task 1: Advisory
            if hasattr(result, 'tasks_output') and len(result.tasks_output) > 1:
                advisory_output_raw = result.tasks_output[1].raw
                
                # Clean up json string if it has markdown code blocks
                clean_json = advisory_output_raw.replace("```json", "").replace("```", "").strip()
                
                advisory_data = json.loads(clean_json)
                
                st.markdown("---")
                st.subheader("🛡️ Strategic Legal Advice")
                
                # Severity Badge
                severity = advisory_data.get('severity', 'Unknown')
                legal_type = advisory_data.get('legal_type', 'General')
                action = advisory_data.get('recommended_action', 'Review Case')
                guidance = advisory_data.get('step_guidance', 'Please consult a lawyer.')

                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.info(f"**Severity**: {severity}")
                with col_b:
                    st.warning(f"**Type**: {legal_type}")
                with col_c:
                    st.error(f"**Action**: {action}")
                
                st.markdown(f"**👉 Immediate Step Guidance:**\n> {guidance}")
                st.markdown("---")

        except Exception as e:
            # Fallback if parsing fails, just don't show the special section
            print(f"DEBUG: Could not parse advisory JSON: {e}")
            pass
        # ---------------------------------------------------

        st.subheader("📄 Final Legal Document")
        final_result = str(result)
        st.markdown(final_result)

        # Optionally send the final document via email
        if send_lawyer_email:
            if not lawyer_email or "@" not in lawyer_email:
                st.warning("Please enter a valid lawyer email address to send the document.")
            else:
                subject = "Consultation Request — Legal Document"
                body = final_result
                from tools.email_tool import send_email_smtp
                email_res = send_email_smtp(to_email=lawyer_email, subject=subject, body=body)
                if email_res.get("ok"):
                    st.success(f"✅ Email sent to {lawyer_email}")
                else:
                    st.error(f"❌ Email failed: {email_res.get('error', 'Unknown error')}")
        
        # Show all intermediate outputs if available
        if hasattr(result, 'tasks_output'):
            with st.expander("📊 View All Task Outputs", expanded=False):
                for i, task_output in enumerate(result.tasks_output, 1):
                    st.markdown(f"### Task {i} Output")
                    st.text(task_output.raw)
                    st.markdown("---")
        elif hasattr(result, 'tasks'):
            with st.expander("📊 View All Task Outputs", expanded=False):
                for i, task in enumerate(result.tasks, 1):
                    if hasattr(task, 'output'):
                        st.markdown(f"### Task {i} Output")
                        st.text(str(task.output))
                        st.markdown("---")
