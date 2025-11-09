import streamlit as st
import os
import json
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

# Initialize session state with PDF processing
if "agent" not in st.session_state:
    with st.spinner("🔄 Initializing agent and processing PDFs..."):
        try:
            from utils.pdf_processor import PDFProcessor
            
            # Check for PDFs
            if not os.path.exists("pdfs"):
                st.error("❌ 'pdfs' folder not found!")
                st.stop()
            
            pdf_files = [f for f in os.listdir("pdfs") if f.endswith('.pdf')]
            
            if not pdf_files:
                st.error("❌ No PDF files found in 'pdfs' folder!")
                st.stop()
            
            st.info(f"📚 Found {len(pdf_files)} PDF(s): {', '.join(pdf_files)}")
            
            # Initialize processor
            processor = PDFProcessor()
            
            # Always process PDFs on cloud (since ChromaDB doesn't persist)
            if processor.is_cloud or not os.path.exists("data/chroma_db"):
                with st.spinner("📄 Processing PDFs (this takes ~30 seconds)..."):
                    success = processor.process_all_pdfs()
                    
                    if not success:
                        st.error("❌ Failed to process PDFs!")
                        st.stop()
                    
                    st.success("✅ PDFs processed successfully!")
            else:
                processor.load_vectorstore()
            
            # Now initialize agent
            st.session_state.agent = PDFQAAgent()
            st.session_state.messages = []
            st.success("✅ Agent ready!")
            
        except Exception as e:
            st.error(f"❌ Error initializing: {str(e)}")
            st.exception(e)
            st.stop()

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