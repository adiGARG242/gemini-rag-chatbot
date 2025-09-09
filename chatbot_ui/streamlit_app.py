import requests
import streamlit as st

# FastAPI backend URL
import os

# Use env var if available, else default to localhost
API_URL = os.getenv("API_URL", "http://localhost:8000/chat")

st.set_page_config(page_title="🏥 Gemini RAG Chatbot", layout="centered")
st.title("🏥 Gemini RAG Chatbot")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Display chat history
for msg in st.session_state["messages"]:
    role, text = msg
    if role == "user":
        st.markdown(f"**🧑 You:** {text}")
    else:
        st.markdown(f"**🤖 Bot:** {text}")

# Input box
question = st.text_input("Ask me anything about hospitals, patients, or reviews:")

if st.button("Send") and question:
    # Add user message
    st.session_state["messages"].append(("user", question))

    # Call FastAPI
    try:
        response = requests.post(API_URL, json={"question": question})
        data = response.json()
        answer = data.get("answer", "⚠️ No response from API")
    except Exception as e:
        answer = f"⚠️ Error: {str(e)}"

    # Add bot reply
    st.session_state["messages"].append(("bot", answer))
    st.rerun()
