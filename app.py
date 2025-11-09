import streamlit as st
import os
import json
import re
from dotenv import load_dotenv
from agent import PDFQAAgent

load_dotenv()

st.set_page_config(
    page_title="PDF Q&A Agent",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful styling
st.markdown("""
<style>
    .main {
        max-width: 1200px;
    }
    .chat-message {
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #1976d2;
    }
    .assistant-message {
        background-color: #f5f5f5;
        border-left: 4px solid #4caf50;
    }
    .security-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
        font-weight: 500;
    }
    h1 {
        color: #1976d2;
        text-align: center;
    }
    .source-citation {
        background-color: #fff3cd;
        padding: 10px;
        border-radius: 5px;
        margin-top: 10px;
        border-left: 4px solid #ffc107;
        font-size: 0.9em;
        color: #856404;
    }
</style>
""", unsafe_allow_html=True)

st.title("📄  Medium Scale Developers Association")

st.markdown("""
<div class="security-badge">
🔒 <strong>Founder & President : Mr. Milind Shripati Patil
</div>
""", unsafe_allow_html=True)

# Initialize session state
if "agent" not in st.session_state:
    with st.spinner("🔄 Initializing agent..."):
        st.session_state.agent = PDFQAAgent()
        st.session_state.messages = []

if "messages" not in st.session_state:
    st.session_state.messages = []

def parse_response(response_text):
    """Parse and clean response text, removing JSON artifacts"""
    response_text = str(response_text).strip()
    
    # If it's a JSON list, extract the text field
    if response_text.startswith("["):
        try:
            data = json.loads(response_text)
            if isinstance(data, list) and len(data) > 0:
                for item in data:
                    if isinstance(item, dict) and 'text' in item:
                        return item['text']
        except (json.JSONDecodeError, TypeError, IndexError):
            pass
    
    # If it's a JSON object with 'text' field
    if response_text.startswith("{"):
        try:
            data = json.loads(response_text)
            if isinstance(data, dict) and 'text' in data:
                return data['text']
        except (json.JSONDecodeError, TypeError):
            pass
    
    return response_text

def display_message(role, content):
    """Display a chat message with proper formatting"""
    content = parse_response(content)
    
    if role == "user":
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>You:</strong><br>{content}
        </div>
        """, unsafe_allow_html=True)
    else:
        # For assistant messages, display as markdown without the wrapper
        st.markdown(content)

# Sidebar controls
with st.sidebar:
    st.header("⚙️ Controls")
    
    col1, col2 = st.columns(2)
    # with col1:
    #     if st.button("📋 List PDFs", use_container_width=True):
    #         st.session_state.messages.append({"role": "user", "content": "📋 List PDFs"})
    #         with st.spinner("📚 Retrieving PDFs..."):
    #             response = st.session_state.agent.ask("List all available PDFs")
    #             st.session_state.messages.append({"role": "assistant", "content": response})
    #         st.rerun()
    
    # with col2:
    #     if st.button("🖼️ List Images", use_container_width=True):
    #         st.session_state.messages.append({"role": "user", "content": "🖼️ List Images"})
    #         with st.spinner("🖼️ Retrieving images..."):
    #             response = st.session_state.agent.ask("List all available images")
    #             st.session_state.messages.append({"role": "assistant", "content": response})
    #         st.rerun()
    
    st.divider()
    
    if st.button("🔄 Reset Chat", use_container_width=True):
        st.session_state.agent.reset()
        st.session_state.messages = []
        st.success("✅ Chat reset!")
        st.rerun()
    
    if st.button("🗑️ Clear All Messages", use_container_width=True):
        st.session_state.messages = []
        st.success("✅ All messages cleared!")
        st.rerun()
    
    st.divider()
    
    # st.markdown("""
    # ### 🔒 Security Model:
    # - ✅ PDF processing: LOCAL
    # - ✅ Image storage: LOCAL
    # - ✅ Embeddings: LOCAL
    # - ✅ Search/Retrieval: LOCAL
    # - ⚠️ Only relevant chunks sent to Claude
    
    # ### 📝 Tips:
    # - Ask questions about your PDFs
    # - Use "analyze [filename]" for images
    # - Use "find shape [filename]" to search
    # - Click "Reset Chat" to start fresh
    # """)

# Display chat history
st.subheader("💬 Conversation")

if len(st.session_state.messages) == 0:
    st.info("👋 Hello! Ask me anything about MSDA.")

for message in st.session_state.messages:
    display_message(message["role"], message["content"])

# Chat input at the bottom
st.divider()
user_input = st.chat_input("Ask a question about MSDA")

if user_input:
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Display user message immediately
    display_message("user", user_input)
    
    # Get response from agent
    with st.spinner("⏳ Processing your question..."):
        response = st.session_state.agent.ask(user_input)
    
    # Add assistant message to history
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Display assistant response
    display_message("assistant", response)
    
    st.rerun()