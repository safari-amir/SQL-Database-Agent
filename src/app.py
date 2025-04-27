import os
import streamlit as st
from workflow import app
from database import SessionLocal
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import *

# Fake configuration to simulate a current user context
fake_config = {
    "configurable": {
        "current_user_id": "1"
    }
}

# Set Streamlit page configuration
st.set_page_config(
    page_title="🍽️ Restaurant Chatbot",
    page_icon="🍔",
    layout="centered"
)

# Streamlit app title and description
st.title("🍽️ Welcome to ChatFood Restaurant!")
st.caption("🛎️ Your personal assistant for ordering delicious food.")

# Initialize session state to store chat messages
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "👋 Hello! Welcome to ChatFood Restaurant.\n\nWhat would you like to order today? 🍕🍔🥗"}
    ]

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle new user input
if prompt := st.chat_input("Type your order here... 🍽️"):
    # Save user message
    st.session_state.messages.append({"role": "user", "content": f"🧑‍🍳 {prompt}"})

    with st.chat_message("user"):
        st.markdown(f"🧑‍🍳 {prompt}")

    # Only send the current user's message to the model
    current_message = f"user: {prompt}"

    # Call the backend model
    response = app.invoke(
        {"question": current_message, "attempts": 0},
        config=fake_config
    )

    # Get the assistant's reply
    assistant_reply = response["query_result"]

    # Add some friendly touch if you want
    assistant_reply = "🍽️ " + assistant_reply

    # Save assistant reply
    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

    with st.chat_message("assistant"):
        st.markdown(assistant_reply)
