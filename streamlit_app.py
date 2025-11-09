# Add debug section (temporary)
with st.expander("🔍 Debug Info", expanded=True):
    import os
    from pathlib import Path
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**PDF Directory**")
        if os.path.exists("pdfs"):
            pdfs = [f for f in os.listdir("pdfs") if f.endswith('.pdf')]
            st.write(f"Found {len(pdfs)} PDFs:")
            for pdf in pdfs:
                size = os.path.getsize(f"pdfs/{pdf}") / (1024*1024)
                st.write(f"- {pdf} ({size:.1f} MB)")
        else:
            st.error("❌ pdfs/ folder not found!")
    
    with col2:
        st.write("**Vector Database**")
        chroma_exists = os.path.exists("data/chroma_db")
        st.write(f"ChromaDB exists: {chroma_exists}")
        
        if 'agent' in st.session_state:
            try:
                from tools.pdf_tools import processor
                if processor and processor.vectorstore:
                    st.success("✅ Vectorstore loaded")
                else:
                    st.error("❌ Vectorstore is None")
            except:
                st.warning("⚠️ Can't check vectorstore")
    
    with col3:
        st.write("**Environment**")
        st.write(f"Cloud: {'STREAMLIT_RUNTIME_ENV' in os.environ}")
        st.write(f"CWD: {os.getcwd()}")