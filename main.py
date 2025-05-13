import streamlit as st
import google.generativeai as genai
import json
import fitz  # PyMuPDF
import traceback
import re

st.set_page_config(page_title="PDF MCQ Generator", layout="wide")
st.title("📄 PDF to MCQ Generator")

# Session state initialization
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""
if "mcqs" not in st.session_state:
    st.session_state.mcqs = []
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "checked" not in st.session_state:
    st.session_state.checked = {}
if "score_shown" not in st.session_state:
    st.session_state.score_shown = False

# Sidebar - API Key input
st.sidebar.header("Upload & Settings")
api_key = st.sidebar.text_input("🔐 Enter Google API Key", type="password")

# Sidebar - File uploader
uploaded_files = st.sidebar.file_uploader("📁 Upload PDF files", accept_multiple_files=True, type="pdf")

# Button to process PDF files
if st.sidebar.button("Process PDFs"):
    if uploaded_files:
        with st.spinner("📚 Extracting text from PDFs..."):
            text = ""
            for uploaded_file in uploaded_files:
                try:
                    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                    for page in doc:
                        text += page.get_text()
                except Exception as e:
                    st.error(f"Error reading {uploaded_file.name}: {e}")
            st.session_state.pdf_text = text
            if text:
                st.success("✅ Text extracted successfully!")
            else:
                st.error("❌ Failed to extract text.")

# Generate MCQs
if st.sidebar.button("Generate MCQ Quiz"):
    if not api_key:
        st.sidebar.error("Please enter your Google API key.")
    elif not st.session_state.pdf_text:
        st.sidebar.error("Please process PDFs first.")
    else:
        genai.configure(api_key=api_key)
        prompt = f"""
You are an AI that generates 10 multiple choice questions from the following text. Each question should have:
- The question
- 4 options labeled A, B, C, D
- The correct option (like "A" or "C")

Return the result as a JSON list with this structure:
[
  {{
    "question": "....",
    "options": {{
      "A": "...",
      "B": "...",
      "C": "...",
      "D": "..."
    }},
    "answer": "B"
  }},
  ...
]

Text:
{st.session_state.pdf_text[:12000]}
"""
        model = genai.GenerativeModel("gemini-1.5-flash")
        try:
            with st.spinner("🧠 Generating MCQs with Gemini..."):
                response = model.generate_content(prompt)
                text_response = response.text.strip()
                clean_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text_response)
                mcqs = json.loads(clean_text)
                st.session_state.mcqs = mcqs
                st.session_state.answers = {}
                st.session_state.checked = {}
                st.session_state.score_shown = False
                st.success("✅ MCQs generated!")
        except Exception:
            st.error("❌ Failed to generate MCQs.")
            st.code(traceback.format_exc())

# Show MCQs
if st.session_state.mcqs:
    st.subheader("📝 Answer the questions below:")

    for i, q in enumerate(st.session_state.mcqs):
        st.markdown(f"**Q{i+1}: {q['question']}**")
        options = q["options"]

        # Radio to select answer
        selected = st.radio(
            f"Choose an answer for Q{i+1}",
            list(options.keys()),
            format_func=lambda x: f"{x}. {options[x]}",
            key=f"radio_{i}"
        )

        st.session_state.answers[i] = selected

        # Check Answer button (sets flag in session_state)
        if st.button(f"Check Q{i+1}", key=f"btn_check_{i}"):
            st.session_state.checked[i] = True

        # If already checked, show result
        if st.session_state.checked.get(i):
            if selected == q["answer"]:
                st.success("🎉 Correct!")
            else:
                st.error(f"❌ Incorrect. Correct answer: {q['answer']} — {options[q['answer']]}")

    # Show final score
    if st.button("🎯 Show Score"):
        correct = sum(
            1 for i, q in enumerate(st.session_state.mcqs)
            if st.session_state.answers.get(i) == q["answer"]
        )
        total = len(st.session_state.mcqs)
        st.session_state.score_shown = True
        st.success(f"Your Score: {correct} / {total}")

    elif st.session_state.score_shown:
        correct = sum(
            1 for i, q in enumerate(st.session_state.mcqs)
            if st.session_state.answers.get(i) == q["answer"]
        )
        total = len(st.session_state.mcqs)
        st.success(f"Your Score: {correct} / {total}")
