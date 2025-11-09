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