import streamlit as st
import google.generativeai as genai
import json
import fitz  # PyMuPDF
import traceback
import re

st.set_page_config(page_title="PDF MCQ Generator", layout="wide")
st.title("📄 PDF to MCQ Generator")

# Session state initialization
for key in ["pdf_text", "mcqs", "answers", "checked", "score_shown", "question_count"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key in ["mcqs", "answers", "checked"] else 0 if key == "question_count" else False if key == "score_shown" else ""

# Sidebar - Settings
st.sidebar.header("Upload & Settings")
api_key = st.sidebar.text_input("🔐 Enter Google API Key", type="password")
uploaded_files = st.sidebar.file_uploader("📁 Upload PDF files", accept_multiple_files=True, type="pdf")
st.session_state.question_count = st.sidebar.number_input("🔢 Number of Questions", min_value=1, max_value=50, value=10, step=1)

# Process PDFs
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
You are an AI that generates {st.session_state.question_count} multiple choice questions from the following text. Each question should have:
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
{st.session_state.pdf_text}
"""

        model = genai.GenerativeModel("gemini-1.5-flash")
        try:
            with st.spinner("🧠 Generating MCQs with Gemini..."):
                response = model.generate_content(prompt)
                text_response = response.text.strip()
                clean_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text_response)
                mcqs = json.loads(clean_text)

                # Reset and store MCQs
                st.session_state.mcqs = mcqs
                st.session_state.answers = {}
                st.session_state.checked = {}
                st.session_state.score_shown = False
                st.success("✅ MCQs generated!")
        except Exception:
            st.error("❌ Failed to generate MCQs.")
            st.code(traceback.format_exc())

# Show MCQs and handle interactions
if st.session_state.mcqs:
    st.subheader("📝 Answer the questions below:")

    for i, q in enumerate(st.session_state.mcqs):
        st.markdown(f"**Q{i+1}: {q['question']}**")
        options = q["options"]

        # If answer is checked, lock the radio input
        if st.session_state.checked.get(i):
            st.radio(
                f"Your answer for Q{i+1}",
                list(options.keys()),
                format_func=lambda x: f"{x}. {options[x]}",
                index=list(options.keys()).index(st.session_state.answers[i]),
                key=f"radio_{i}",
                disabled=True
            )
        else:
            selected = st.radio(
                f"Choose an answer for Q{i+1}",
                list(options.keys()),
                format_func=lambda x: f"{x}. {options[x]}",
                key=f"radio_{i}"
            )
            st.session_state.answers[i] = selected

            if st.button(f"Check Q{i+1}", key=f"btn_check_{i}"):
                st.session_state.checked[i] = True

        # Show result if already checked
        if st.session_state.checked.get(i):
            correct = q["answer"]
            user_ans = st.session_state.answers[i]
            if user_ans == correct:
                st.success("🎉 Correct!")
            else:
                st.error(f"❌ Incorrect. Correct answer: {correct} — {options[correct]}")

    # Show total score
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
