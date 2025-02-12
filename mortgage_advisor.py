import streamlit as st
from mortgage_assistant import ConversationalMortgageAgent

def initialize_chat():
    """Initialize chat session and welcome message"""
    if 'mortgage_agent' not in st.session_state:
        st.session_state['mortgage_agent'] = ConversationalMortgageAgent()
        welcome_msg = "Hello! I'm your mortgage advisor. I'm here to help you find the right mortgage solution. What brings you in today?"
        st.session_state['messages'] = [{"role": "assistant", "content": welcome_msg}]

def main():
    st.set_page_config(
        page_title="AI Mortgage Advisor",
        page_icon="🏠",
        layout="centered"
    )

    st.markdown("""
        <style>
        .stApp {background-color: #f5f7f9;}
        div.stChatMessage {
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
        .user-message {background-color: #e3f2fd;}
        .assistant-message {background-color: white;}
        h1 {color: #1e3a8a;}
        .stChatInputContainer {
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: white;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("🏠 AI Mortgage Advisor")
    initialize_chat()  # Add this line
    
    if 'mortgage_agent' not in st.session_state:
        st.session_state['mortgage_agent'] = ConversationalMortgageAgent()
        welcome_msg = "Hello! I'm your mortgage advisor. How can I help you today?"
        st.session_state['messages'] = [{"role": "assistant", "content": welcome_msg}]

    for message in st.session_state['messages']:
        with st.chat_message(message["role"]):
            st.markdown(f"<div class='{message['role']}-message'>{message['content']}</div>", 
                       unsafe_allow_html=True)

    if user_input := st.chat_input("Type your message here..."):
        with st.chat_message("user"):
            st.markdown(f"<div class='user-message'>{user_input}</div>", 
                       unsafe_allow_html=True)
        
        agent = st.session_state['mortgage_agent']
        response = agent.get_next_response(user_input)
        
        with st.chat_message("assistant"):
            st.markdown(f"<div class='assistant-message'>{response}</div>", 
                       unsafe_allow_html=True)
        
        st.session_state['messages'].extend([
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": response}
        ])

if __name__ == "__main__":
    main()