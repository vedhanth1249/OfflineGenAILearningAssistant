import streamlit as st
import ollama
import json
from pdf_processor import extract_text_from_pdf

st.set_page_config(page_title="Offline GenAI Learning Assistant",
                   page_icon="📚",
                   layout="wide")

st.markdown("""
<style>

/* Main App */
.stApp {
    background: #0B1120;
    color: #FFFFFF;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #111827;
}

/* Titles */
h1, h2, h3 {
    color: #FFFFFF !important;
}

/* Normal text */
p, span, label {
    color: #E5E7EB !important;
}

/* Selectbox */
.stSelectbox label {
    color: white !important;
}

.stSelectbox div[data-baseweb="select"] {
    background-color: #1F2937 !important;
    color: white !important;
    border-radius: 10px;
}

/* Dropdown text */
.stSelectbox div {
    color: white !important;
}

/* Radio Buttons */
.stRadio label {
    color: white !important;
}

/* Text Input */
.stTextInput input {
    background: #1F2937 !important;
    color: white !important;
    border-radius: 10px;
}

/* Text Area */
.stTextArea textarea {
    background: #1F2937 !important;
    color: white !important;
}

/* Buttons */
.stButton button {
    background: linear-gradient(
        135deg,
        #2563EB,
        #7C3AED
    );
    color: white !important;
    border: none;
    border-radius: 10px;
    font-weight: bold;
}

/* Statistics Cards */
.stat-card {
    background: #1F2937;
    color: white;
    padding: 20px;
    border-radius: 15px;
    text-align: center;
    border: 1px solid #374151;
}

/* Quiz Question Card */
.quiz-card {
    background: #1F2937;
    color: white;
    padding: 18px;
    border-radius: 12px;
    font-size: 22px;
    font-weight: bold;
    margin-bottom: 10px;
}

/* Flash Cards */
.flash-card {
    background: #1F2937;
    color: white;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #374151;
}

/* File name */
small {
    font-size: 12px !important;
    color: #9CA3AF !important;
}
</style>
""", unsafe_allow_html=True)


st.title("📚 Offline GenAI Learning Assistant")

uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

if uploaded_file:

    text = extract_text_from_pdf(uploaded_file)

    with st.sidebar:
        st.title("📚 Features")

        action = st.radio(
            "Choose Feature",
            [
                "📄 Summary",
                "❓ Quiz",
                "🧠 Flash Cards",
                "💬 Ask Questions"
            ]
        )

        st.divider()
        st.caption(f"📄 {uploaded_file.name}")
        st.caption("🤖 Model: llama3")

    st.success("PDF Uploaded Successfully")

    if action == "📄 Summary":

        st.subheader("📄 Summary")

        if st.button("Generate Summary"):

            with st.spinner("Generating Summary..."):

                response = ollama.chat(
                    model="llama3",
                    messages=[{
                        "role":"user",
                        "content":f"Summarize these notes in simple bullet points:\n\n{text[:5000]}"
                    }]
                )

                st.write(response["message"]["content"])

    elif action == "❓ Quiz":

        st.subheader("❓ Quiz Generator")

        if st.button("Generate Quiz"):

            prompt = f"""
Create 5 MCQs from the content.

Return ONLY JSON.

[
 {{
  "question":"Question",
  "options":["A","B","C","D"],
  "answer":"A"
 }}
]

Content:
{text[:4000]}
"""
            response = ollama.chat(
                model="llama3",
                messages=[{"role":"user","content":prompt}]
            )

            quiz_text = response["message"]["content"]

            try:
                start = quiz_text.find("[")
                end = quiz_text.rfind("]") + 1

                st.session_state.quiz = json.loads(
                    quiz_text[start:end]
                )
                st.session_state.score = 0
                st.session_state.checked = []

            except:
                st.error("Quiz generation failed")
                st.code(quiz_text)

        if "quiz" in st.session_state:

            total = len(st.session_state.quiz)

            c1,c2 = st.columns(2)

            with c1:
                st.markdown(
                    f"<div class='stat-card'><h3>Score</h3><h2>{st.session_state.get('score',0)}</h2></div>",
                    unsafe_allow_html=True
                )

            with c2:
                st.markdown(
                    f"<div class='stat-card'><h3>Total Questions</h3><h2>{total}</h2></div>",
                    unsafe_allow_html=True
                )

            for i,q in enumerate(st.session_state.quiz):

                st.markdown(
                    f"<div class='quiz-card'><b>Q{i+1}. {q['question']}</b></div>",
                    unsafe_allow_html=True
                )

                selected = st.radio(
                    f"Select answer {i+1}",
                    q["options"],
                    key=f"radio_{i}"
                )

                if st.button(f"Check Q{i+1}", key=f"btn_{i}"):

                    if selected.strip().lower() == q["answer"].strip().lower():

                        st.success("✅ Correct")

                        if i not in st.session_state.get("checked", []):
                            st.session_state.score += 1
                            st.session_state.checked.append(i)

                    else:
                        st.error("❌ Wrong")
                        st.info(f"Correct Answer: {q['answer']}")

                st.divider()

    elif action == "🧠 Flash Cards":

        st.subheader("🧠 Flash Cards")

        if st.button("Generate Flash Cards"):

            response = ollama.chat(
                model="llama3",
                messages=[{
                    "role":"user",
                    "content":f"""
Create 10 flash cards.

Return JSON only.

[
 {{
  "question":"Question",
  "answer":"Answer"
 }}
]

{text[:4000]}
"""
                }]
            )

            try:

                txt = response["message"]["content"]
                start = txt.find("[")
                end = txt.rfind("]") + 1

                st.session_state.cards = json.loads(txt[start:end])

            except:
                st.error("Failed to generate flash cards")

        if "cards" in st.session_state:

            for i,card in enumerate(st.session_state.cards):

                with st.expander(f"🃏 Flash Card {i+1}"):

                    st.markdown(
                        f"<div class='flash-card'><h4>{card['question']}</h4><hr><p>{card['answer']}</p></div>",
                        unsafe_allow_html=True
                    )

    elif action == "💬 Ask Questions":

        st.subheader("💬 Ask Questions")

        question = st.text_input("Enter your question")

        if st.button("Get Answer") and question:

            response = ollama.chat(
                model="llama3",
                messages=[{
                    "role":"user",
                    "content":f"""
Use the content below to answer.

Content:
{text[:5000]}

Question:
{question}
"""
                }
                ]
            )

            st.write(response["message"]["content"])
