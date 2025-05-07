import streamlit as st
from agent.workflow import app
from langgraph.types import Command
import uuid

# -------------------------
# 1) Session State Setup
# -------------------------
def init_session():
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant",
            "content": "👋 Hello! Welcome to ChatFood Restaurant.\n\nWhat would you like to order today? 🍕🍔🥗"
        }]
    if "awaiting_confirmation" not in st.session_state:
        st.session_state.awaiting_confirmation = False
        st.session_state.confirmation_response = None

def reset_confirmation_state():
    st.session_state.awaiting_confirmation = False
    st.session_state.confirmation_response = None
    new_tid = str(uuid.uuid4())
    st.session_state.thread_id = new_tid

# -------------------------
# 2) App Configuration
# -------------------------
init_session()

config = {
    "configurable": {
        "thread_id": st.session_state.thread_id,
        "current_user_id": "2"
    }
}

st.set_page_config(page_title="🍽️ Restaurant Chatbot", page_icon="🍔", layout="centered")
st.title("🍽️ Welcome to ChatFood Restaurant!")
st.caption("🛎️ Your personal assistant for ordering delicious food.")

# -------------------------
# 3) Display Chat History
# -------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -------------------------
# 4) Handle User Input
# -------------------------
if prompt := st.chat_input("Type your order here... 🍽️"):
    user_msg = f"🧑‍🍳 {prompt}"
    st.session_state.messages.append({"role": "user", "content": user_msg})
    with st.chat_message("user"):
        st.markdown(user_msg)

    response = app.invoke({"question": f"user: {prompt}", "attempts": 0}, config=config)

    if isinstance(response, dict) and "query_result" in response:
        assistant_msg = "🍽️ " + response["query_result"]
        st.session_state.messages.append({"role": "assistant", "content": assistant_msg})
        with st.chat_message("assistant"):
            st.markdown(assistant_msg)
        reset_confirmation_state()
    else:
        st.session_state.awaiting_confirmation = True
        st.session_state.confirmation_response = None

# -------------------------
# 5) Show Confirmation UI
# -------------------------
if st.session_state.awaiting_confirmation:
    with st.chat_message("assistant"):
        st.markdown("Are you ready to confirm your order❓")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Yes"):
            st.session_state.confirmation_response = "Yes"
    with col2:
        if st.button("❌ No"):
            st.session_state.confirmation_response = "No"

# -------------------------
# 6) Handle Confirmation
# -------------------------
if st.session_state.confirmation_response:
    response = app.invoke(Command(resume=st.session_state.confirmation_response), config=config)
    assistant_msg = "🍽️ " + response["query_result"]
    st.session_state.messages.append({"role": "assistant", "content": assistant_msg})
    with st.chat_message("assistant"):
        st.markdown(assistant_msg)
    reset_confirmation_state()
