import os
import shutil
from agent import PDFQAAgent
from utils.pdf_processor import PDFProcessor

def setup_pdfs():
    print("\n" + "="*60)
    print("PDF PROCESSING SETUP (100% LOCAL)")
    print("="*60)
    print("🔒 All PDF processing happens on YOUR computer")
    print("🔒 No data sent to cloud during this step")
    print("="*60 + "\n")
    
    processor = PDFProcessor()
    
    if os.path.exists("data/chroma_db"):
        response = input("\nVector database exists. Reprocess? (yes/no): ")
        if response.lower() != 'yes':
            print("Using existing local database...")
            return
    
    print("\n📄 Processing PDFs locally...")
    success = processor.process_all_pdfs()
    
    if success:
        print("\n✅ PDFs processed successfully!")
        print("🔒 All data stored LOCALLY in: data/chroma_db/")
        print("🔒 No data has been sent to any cloud service yet\n")
    else:
        print("\n❌ Failed. Add PDFs to 'pdfs' folder.")

def upload_image():
    """Upload an image file to the images directory"""
    print("\n" + "="*60)
    print("IMAGE UPLOAD (100% LOCAL)")
    print("="*60)
    
    if not os.path.exists("images"):
        os.makedirs("images")
    
    image_path = input("Enter the full path to your image file: ").strip()
    
    if not os.path.exists(image_path):
        print("❌ File not found!")
        return
    
    # Check if it's a valid image
    valid_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')
    if not image_path.lower().endswith(valid_extensions):
        print(f"❌ Invalid image format. Supported: {', '.join(valid_extensions)}")
        return
    
    # Copy to images directory
    filename = os.path.basename(image_path)
    destination = os.path.join("images", filename)
    
    try:
        shutil.copy2(image_path, destination)
        print(f"✅ Image uploaded successfully: {filename}")
        print(f"🔒 Stored locally in: images/{filename}\n")
    except Exception as e:
        print(f"❌ Error uploading image: {str(e)}")

def main():
    print("\n" + "="*60)
    print("SECURE PDF Q&A AGENT WITH IMAGE ANALYSIS")
    print("="*60)
    print("\n🔒 SECURITY MODEL:")
    print("   ✅ Steps 1-5: 100% LOCAL (on your computer)")
    print("      - PDF reading")
    print("      - Text extraction")
    print("      - Embedding creation")
    print("      - Database storage")
    print("      - Search/retrieval")
    print("      - Image storage")
    print("\n   ⚠️  Step 6: Small chunks → Claude")
    print("      - Only relevant text snippets sent")
    print("      - Images sent for analysis only")
    print("      - Full PDF never transmitted")
    print("      - ~500-2000 characters per question")
    print("="*60 + "\n")
    
    if not os.path.exists("pdfs"):
        os.makedirs("pdfs")
    
    if not os.path.exists("images"):
        os.makedirs("images")
    
    if os.path.exists("pdfs") and os.listdir("pdfs") and not os.path.exists("data/chroma_db"):
        print("⚠️  PDFs not processed yet.")
        setup_pdfs()
    
    print("Initializing agent...")
    agent = PDFQAAgent()
    print("✅ Agent ready!\n")
    
    print("Commands:")
    print("  - 'list' - Show all PDFs (stored locally)")
    print("  - 'list images' - Show all uploaded images")
    print("  - 'upload image' - Upload a new image")
    print("  - 'analyze <filename>' - Analyze an image")
    print("  - 'find shape <filename>' - Find shape from image in PDFs")
    print("  - 'reprocess' - Reprocess PDFs (local)")
    print("  - 'reset' - Clear conversation")
    print("  - 'quit' - Exit\n")
    
    while True:
        user_input = input("You: ").strip()
        
        if not user_input:
            continue
        
        if user_input.lower() == 'quit':
            print("Goodbye! 👋")
            break
        
        if user_input.lower() == 'reset':
            agent.reset()
            print("✅ Conversation reset\n")
            continue
        
        if user_input.lower() == 'reprocess':
            setup_pdfs()
            agent = PDFQAAgent()
            print("✅ Agent reloaded\n")
            continue
        
        if user_input.lower() == 'list':
            user_input = "List all available PDF files"
        
        if user_input.lower() == 'list images':
            user_input = "List all available image files"
        
        if user_input.lower() == 'upload image':
            upload_image()
            continue
        
        if user_input.lower().startswith('analyze '):
            filename = user_input[8:].strip()
            user_input = f"Analyze the image file: {filename}"
        
        if user_input.lower().startswith('find shape '):
            filename = user_input[11:].strip()
            user_input = f"Find the shape from image {filename} in the PDF documents"
        
        print("\n" + "="*60)
        print("Processing your question...")
        print("="*60)
        
        answer = agent.ask(user_input)
        
        print("\n" + "="*60)
        print("ANSWER:")
        print("="*60)
        print(f"{answer}\n")
        print("="*60 + "\n")

if __name__ == "__main__":
    main()