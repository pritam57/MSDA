import os
import json
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

# NEW IMPORTS for LangChain 1.0+
from langgraph.prebuilt import create_react_agent

from tools.pdf_tools import search_pdfs, list_available_pdfs, list_available_images, analyze_image, find_shape_in_pdfs

load_dotenv()

class PDFQAAgent:
    def __init__(self):
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=0.3
        )
        
        self.tools = [
            search_pdfs, 
            list_available_pdfs, 
            list_available_images,
            analyze_image,
            find_shape_in_pdfs
        ]
        
        # Create the system prompt
        self.system_prompt = """You are a helpful AI assistant that answers questions based on PDF documents and can analyze images.

CRITICAL FORMATTING RULES:
- ALWAYS format your response in clean, readable markdown
- Use headers (##, ###) for sections
- Use bullet points and numbered lists
- Format all content as readable text
- NEVER include raw JSON, lists in brackets, or data structures
- Always cite sources with document names and page numbers
- Be conversational and helpful
- Use proper spacing and line breaks for clarity

Your job is to:
- Answer questions based ONLY on the provided text chunks from PDFs
- Analyze images when provided
- Find shapes from images in PDF documents
- Present information in a clear, readable format
- Cite sources properly"""
        
        # Create agent using langgraph
        self.agent_executor = create_react_agent(
            self.llm, 
            self.tools,
            prompt=self.system_prompt  # FIXED: Changed from state_modifier to prompt
        )
        
        self.chat_history = []
    
    def _extract_text_from_json(self, response_text):
        """Extract text field from JSON response"""
        response_text = str(response_text).strip()
        
        # Handle JSON list format: [{'text': '...', 'type': 'text', ...}]
        if response_text.startswith("["):
            try:
                data = json.loads(response_text)
                if isinstance(data, list) and len(data) > 0:
                    for item in data:
                        if isinstance(item, dict):
                            if 'text' in item:
                                return item['text']
                            # Try to find any text-like content
                            for key, value in item.items():
                                if isinstance(value, str) and len(value) > 20:
                                    return value
            except (json.JSONDecodeError, TypeError, KeyError):
                pass
        
        # Handle JSON object format: {'text': '...', 'type': 'text', ...}
        if response_text.startswith("{"):
            try:
                data = json.loads(response_text)
                if isinstance(data, dict):
                    if 'text' in data:
                        return data['text']
                    # Try to find any text-like content
                    for key, value in data.items():
                        if isinstance(value, str) and len(value) > 20:
                            return value
            except (json.JSONDecodeError, TypeError, KeyError):
                pass
        
        return response_text
    
    def _clean_text(self, text):
        """Clean and format the text for better readability"""
        # Remove escape sequences like \n and replace with actual newlines
        text = text.replace("\\n", "\n")
        text = text.replace("\\t", "\t")
        text = text.replace("\\\\", "\\")
        
        # Clean up multiple spaces
        lines = text.split("\n")
        cleaned_lines = [line.strip() for line in lines if line.strip()]
        
        return "\n".join(cleaned_lines)
    
    def ask(self, question: str) -> str:
        """Ask a question about msda"""
        try:
            # Invoke the agent with the new API
            response = self.agent_executor.invoke({
                "messages": [("user", question)]
            })
            
            # Extract the response from messages
            if "messages" in response:
                messages = response["messages"]
                # Get the last AI message
                for msg in reversed(messages):
                    if hasattr(msg, 'content') and msg.content:
                        output = msg.content
                        break
                else:
                    output = str(response)
            else:
                output = str(response)
            
            # Extract text from JSON if present
            output = self._extract_text_from_json(output)
            
            # Clean and format the text
            output = self._clean_text(output)
            
            # Store in history
            self.chat_history.append(("human", question))
            self.chat_history.append(("ai", output))
            
            return output
        
        except Exception as e:
            error_msg = str(e)
            if "max iterations" in error_msg.lower():
                return "❌ Sorry, I had trouble processing your question. Please try rephrasing it."
            return f"❌ Error: {str(e)}"
    
    def reset(self):
        """Clear conversation history"""
        self.chat_history = []