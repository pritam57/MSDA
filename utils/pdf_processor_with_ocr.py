import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

class PDFProcessorWithOCR:
    def __init__(self, pdf_directory="pdfs", persist_directory="data/chroma_db"):
        self.pdf_directory = pdf_directory
        self.persist_directory = persist_directory
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.vectorstore = None
    
    def extract_text_from_pdf_with_ocr(self, pdf_path):
        """Extract text from PDF including images using OCR"""
        print(f"Processing {pdf_path} with OCR...")
        
        all_text = []
        
        # First, try to extract regular text
        try:
            loader = PyPDFLoader(pdf_path)
            regular_docs = loader.load()
            
            for doc in regular_docs:
                if doc.page_content.strip():
                    all_text.append({
                        'text': doc.page_content,
                        'page': doc.metadata.get('page', 0),
                        'source': pdf_path,
                        'type': 'text'
                    })
        except Exception as e:
            print(f"Error extracting text: {e}")
        
        # Then, extract text from images using OCR
        try:
            images = convert_from_path(pdf_path)
            
            for page_num, image in enumerate(images):
                print(f"  OCR scanning page {page_num + 1}...")
                
                # Extract text from image
                ocr_text = pytesseract.image_to_string(image)
                
                if ocr_text.strip():
                    all_text.append({
                        'text': ocr_text,
                        'page': page_num,
                        'source': pdf_path,
                        'type': 'ocr'
                    })
        except Exception as e:
            print(f"Error with OCR: {e}")
        
        return all_text
    
    def load_pdfs(self):
        """Load all PDFs with OCR support"""
        print(f"Loading PDFs from {self.pdf_directory}...")
        
        documents = []
        pdf_files = [f for f in os.listdir(self.pdf_directory) if f.endswith('.pdf')]
        
        for pdf_file in pdf_files:
            pdf_path = os.path.join(self.pdf_directory, pdf_file)
            extracted_data = self.extract_text_from_pdf_with_ocr(pdf_path)
            
            for item in extracted_data:
                doc = Document(
                    page_content=item['text'],
                    metadata={
                        'source': item['source'],
                        'page': item['page'],
                        'type': item['type']
                    }
                )
                documents.append(doc)
        
        print(f"✓ Loaded {len(documents)} pages/sections from PDFs")
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