import os
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ImageProcessor:
    def __init__(self, image_dir="images"):
        self.image_dir = image_dir
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)
        
        # Initialize Anthropic client with explicit API key
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=api_key)
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
    
    def analyze_image(self, image_filename: str) -> str:
        """Analyze an image and describe shapes in it"""
        image_path = os.path.join(self.image_dir, image_filename)
        
        if not os.path.exists(image_path):
            return f"Error: Image '{image_filename}' not found in {self.image_dir}/"
        
        # Read and encode image
        try:
            with open(image_path, "rb") as image_file:
                image_data = base64.standard_b64encode(image_file.read()).decode("utf-8")
            
            # Determine media type
            ext = os.path.splitext(image_filename)[1].lower()
            media_type_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.bmp': 'image/bmp'
            }
            media_type = media_type_map.get(ext, 'image/jpeg')
            
            # Call Claude API to analyze image
            print(f"\n🔍 Analyzing image: {image_filename}...")
            print(f"🔒 Image will be sent to Claude API for analysis...")
            
            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": "Describe all shapes in this image in detail. Focus on geometric shapes, their orientation, size relationships, and any distinguishing features. If there are doors, windows, or architectural elements, describe their shapes and configurations."
                            }
                        ],
                    }
                ],
            )
            
            description = message.content[0].text
            print(f"✅ Image analyzed successfully!\n")
            return description
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error analyzing image: {error_msg}\n")
            return f"Error analyzing image: {error_msg}"
    
    def list_images(self):
        """List all images in the image directory"""
        if not os.path.exists(self.image_dir):
            return []
        
        return [f for f in os.listdir(self.image_dir) 
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]