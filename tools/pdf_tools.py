from langchain_core.tools import tool
from utils.pdf_processor import PDFProcessor
from utils.image_processor import ImageProcessor

processor = PDFProcessor()
image_processor = ImageProcessor()

try:
    processor.load_vectorstore()
except:
    pass

@tool
def search_pdfs(query: str) -> str:
    """
    Searches through all uploaded PDFs to find relevant information.
    This search happens LOCALLY on your computer.
    Only the search results (small text chunks) are sent to Claude.
    """
    if not processor.vectorstore:
        return "❌ PDFs have not been processed yet. Please run the setup first."
    
    try:
        results = processor.search(query, k=4)
        
        if not results:
            return f"ℹ️ No relevant information found for '{query}' in the PDFs."
        
        # Format results as readable markdown text (NOT JSON)
        response_lines = [f"## Search Results: '{query}'\n"]
        
        for i, doc in enumerate(results, 1):
            source = doc.metadata.get('source', 'Unknown')
            page = doc.metadata.get('page', 'Unknown')
            content = doc.page_content.strip()
            
            response_lines.append(f"### Result {i}")
            response_lines.append(f"📄 **Source:** {source} | **Page:** {page}")
            response_lines.append(f"\n{content}\n")
            response_lines.append("---\n")
        
        # Join all lines into a single string
        final_response = "\n".join(response_lines)
        return final_response
    
    except Exception as e:
        return f"❌ Error searching PDFs: {str(e)}"

@tool
def list_available_pdfs(dummy: str = "") -> str:
    """Lists all PDF files that have been uploaded and processed."""
    import os
    
    pdf_dir = "pdfs"
    if not os.path.exists(pdf_dir):
        return "❌ PDF directory not found."
    
    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        return "📁 No PDF files found in the pdfs folder."
    
    response_lines = [f"## 📚 Available PDFs ({len(pdf_files)})\n"]
    for pdf in sorted(pdf_files):
        response_lines.append(f"- {pdf}")
    
    return "\n".join(response_lines)

@tool
def list_available_images(dummy: str = "") -> str:
    """Lists all image files that have been uploaded."""
    import os
    
    image_dir = "images"
    if not os.path.exists(image_dir):
        return "📁 No images folder found."
    
    image_files = [f for f in os.listdir(image_dir) 
                   if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
    
    if not image_files:
        return "🖼️ No image files found in the images folder."
    
    response_lines = [f"## 🖼️ Available Images ({len(image_files)})\n"]
    for img in sorted(image_files):
        response_lines.append(f"- {img}")
    
    return "\n".join(response_lines)

@tool
def analyze_image(image_filename: str) -> str:
    """
    Analyzes an uploaded image and describes the shapes found in it.
    This happens LOCALLY on your computer.
    """
    try:
        result = image_processor.analyze_image(image_filename)
        # Make sure result is a string, not a list
        if isinstance(result, list):
            result = "\n".join([str(item) for item in result])
        return str(result)
    except Exception as e:
        return f"❌ Error analyzing image: {str(e)}"

@tool
def find_shape_in_pdfs(image_filename: str) -> str:
    """
    Finds shapes from an uploaded image within PDF documents.
    First analyzes the image locally, then searches PDFs for similar shapes.
    """
    try:
        # Analyze the image first
        shape_description = image_processor.analyze_image(image_filename)
        
        # Make sure it's a string
        if isinstance(shape_description, list):
            shape_description = "\n".join([str(item) for item in shape_description])
        
        if "Error" in str(shape_description) or "not found" in str(shape_description):
            return str(shape_description)
        
        # Search PDFs for this shape
        search_query = f"shape similar to: {shape_description}"
        
        return search_pdfs(search_query)
    except Exception as e:
        return f"❌ Error finding shape in PDFs: {str(e)}"