import streamlit as st
import google.generativeai as genai
import json
import fitz  # PyMuPDF
import traceback
import re

st.set_page_config(page_title="PDF MCQ Generator", layout="wide")
st.title("📄 PDF to MCQ Generator")

# Sidebar - API Key input
st.sidebar.header("Upload & Settings")
api_key = st.sidebar.text_input("🔐 Enter Google API Key", type="password")

# Sidebar - File uploader
uploaded_files = st.sidebar.file_uploader("📁 Upload PDF files", accept_multiple_files=True, type="pdf")

# Button to process PDF files
process_button = st.sidebar.button("Process PDFs")

# Button to generate MCQs
generate_button = st.sidebar.button("Generate MCQ Quiz")

if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""


# Function to extract text from PDFs
def extract_text_from_pdfs(pdf_files):
    text = ""
    for uploaded_file in pdf_files:
        try:
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            for page in doc:
                text += page.get_text()
        except Exception as e:
            st.error(f"Error reading {uploaded_file.name}: {e}")
    return text

# Function to generate MCQs using Gemini
def generate_mcqs(text, api_key):
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
{text[:12000]}
"""

    model = genai.GenerativeModel("gemini-1.5-flash")

    try:
        response = model.generate_content(prompt)

        if not response.text.strip():
            st.error("❌ Gemini returned an empty response.")
            return []

        # Clean response from markdown
        clean_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", response.text.strip())
        mcqs = json.loads(clean_text)
        return mcqs

    except Exception:
        st.error("❌ Failed to generate MCQs.")
        st.code(traceback.format_exc())
        return []

# Process PDF files
if process_button and uploaded_files:
    with st.spinner("📚 Extracting text from PDFs..."):
        st.session_state.pdf_text = extract_text_from_pdfs(uploaded_files)
        if st.session_state.pdf_text:
            st.success("✅ Text extracted successfully!")
        else:
            st.error("❌ Failed to extract text.")


# Generate MCQs
if generate_button:
    if not api_key:
        st.sidebar.error("Please enter your Google API key.")
    elif not st.session_state.pdf_text:

        st.sidebar.error("Please process PDFs first.")
    else:
        with st.spinner("🧠 Generating MCQs with Gemini..."):
            mcqs = generate_mcqs(st.session_state.pdf_text, api_key)

            if mcqs:
                st.success("✅ MCQs generated!")
                for i, q in enumerate(mcqs):
                    st.markdown(f"**Q{i+1}: {q['question']}**")
                    options = q["options"]
                    user_answer = st.radio(
                        f"Choose an answer for Q{i+1}",
                        list(options.keys()),
                        format_func=lambda x: f"{x}. {options[x]}",
                        key=f"q{i+1}"
                    )
                    if st.button(f"Check Q{i+1}", key=f"check{i+1}"):
                        if user_answer == q["answer"]:
                            st.success("🎉 Correct!")
                        else:
                            st.error(f"❌ Incorrect. The correct answer is: {q['answer']}. {options[q['answer']]}")
            else:
                st.error("❌ Failed to generate MCQs. Try again.")
