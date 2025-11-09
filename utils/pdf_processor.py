import os
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter  # FIXED: Updated import
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

class PDFProcessor:
    def __init__(self, pdf_directory="pdfs", persist_directory="data/chroma_db"):
        self.pdf_directory = pdf_directory
        self.persist_directory = persist_directory
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.vectorstore = None
    
    def load_pdfs(self):
        """Load all PDFs from the directory"""
        print(f"Loading PDFs from {self.pdf_directory}...")
        
        loader = DirectoryLoader(
            self.pdf_directory,
            glob="**/*.pdf",
            loader_cls=PyPDFLoader,
            show_progress=True
        )
        
        documents = loader.load()
        print(f"✓ Loaded {len(documents)} pages from PDFs")
        
        return documents
    
    def split_documents(self, documents):
        """Split documents into smaller chunks"""
        print("Splitting documents into chunks...")
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        
        chunks = text_splitter.split_documents(documents)
        print(f"✓ Created {len(chunks)} text chunks")
        
        return chunks
    
    def create_vectorstore(self, chunks):
        """Create vector database from chunks"""
        print("Creating vector database (this may take a few minutes)...")
        
        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        
        print(f"✓ Vector database created and saved to {self.persist_directory}")
    
    def load_vectorstore(self):
        """Load existing vector database"""
        print("Loading existing vector database...")
        
        self.vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings
        )
        
        print("✓ Vector database loaded")
    
    def process_all_pdfs(self):
        """Complete pipeline: load, split, and store PDFs"""
        documents = self.load_pdfs()
        
        if not documents:
            print("No PDFs found! Please add PDF files to the 'pdfs' folder.")
            return False
        
        chunks = self.split_documents(documents)
        self.create_vectorstore(chunks)
        
        return True
    
    def search(self, query, k=4):
        """Search for relevant documents"""
        if not self.vectorstore:
            print("Vector database not loaded!")
            return []
        
        results = self.vectorstore.similarity_search(query, k=k)
        return results