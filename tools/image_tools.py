from langchain_core.tools import tool
from anthropic import Anthropic
import os
from dotenv import load_dotenv
import base64
from PIL import Image
from io import BytesIO

load_dotenv()

# Store uploaded images temporarily
uploaded_images = {}

def image_to_base64(image_path):
    """Convert image file to base64"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

@tool
def upload_image(image_path: str, image_name: str = "uploaded_image") -> str:
    """
    Upload an image to analyze. Provide the full path to the image file.
    The image will be stored and can be referenced in questions.
    
    Args:
        image_path: Full path to the image file
        image_name: Optional name to identify this image
    """
    try:
        # Verify image exists
        if not os.path.exists(image_path):
            return f"Error: Image not found at {image_path}"
        
        # Verify it's an image
        try:
            img = Image.open(image_path)
            img.verify()
        except Exception:
            return "Error: File is not a valid image"
        
        # Store image info
        uploaded_images[image_name] = {
            'path': image_path,
            'base64': image_to_base64(image_path)
        }
        
        return f"✓ Image '{image_name}' uploaded successfully! You can now ask questions about it."
    
    except Exception as e:
        return f"Error uploading image: {str(e)}"

@tool
def analyze_image(question: str, image_name: str = "uploaded_image") -> str:
    """
    Analyze an uploaded image and answer questions about it using Claude Vision.
    The image must be uploaded first using the upload_image tool.
    
    Args:
        question: The question to ask about the image
        image_name: Name of the previously uploaded image (default: "uploaded_image")
    """
    if image_name not in uploaded_images:
        return f"Error: No image named '{image_name}' found. Please upload an image first."
    
    try:
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        image_data = uploaded_images[image_name]
        
        # Detect media type
        image_path = image_data['path']
        if image_path.lower().endswith('.png'):
            media_type = "image/png"
        elif image_path.lower().endswith(('.jpg', '.jpeg')):
            media_type = "image/jpeg"
        elif image_path.lower().endswith('.gif'):
            media_type = "image/gif"
        elif image_path.lower().endswith('.webp'):
            media_type = "image/webp"
        else:
            media_type = "image/png"
        
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data['base64']
                        }
                    },
                    {
                        "type": "text",
                        "text": question
                    }
                ]
            }]
        )
        
        return message.content[0].text
    
    except Exception as e:
        return f"Error analyzing image: {str(e)}"

@tool
def list_uploaded_images(dummy: str = "") -> str:
    """List all currently uploaded images"""
    if not uploaded_images:
        return "No images uploaded yet."
    
    image_list = []
    for name, data in uploaded_images.items():
        image_list.append(f"- {name}: {data['path']}")
    
    return "Uploaded images:\n" + "\n".join(image_list)

@tool
def clear_images(dummy: str = "") -> str:
    """Clear all uploaded images from memory"""
    global uploaded_images
    count = len(uploaded_images)
    uploaded_images = {}
    return f"✓ Cleared {count} uploaded image(s)"