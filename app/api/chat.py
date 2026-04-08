import os
import google.generativeai as genai
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from PyPDF2 import PdfReader
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

router = APIRouter(prefix="/chat", tags=["chat"])

# Configure Gemini
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

class ChatMessage(BaseModel):
    id: Optional[str] = None
    role: str # 'user' or 'assistant'
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []

# Cache for PDF context to avoid reading from disk on every request
cached_context = None

def extract_pdf_context():
    """Extract context from statutes PDF files."""
    global cached_context
    if cached_context is not None:
        return cached_context

    # Try multiple possible locations for the statutes
    # 1. Local development path (if it exists)
    # 2. Relative path for deployment (app/static/statutes or similar)
    possible_paths = [
        r"E:\Software Projects Sineth\WSO2 Ballerina 2025 Competition\lexhub-frontend\public\assets\statutes",
        os.path.join(os.getcwd(), "app", "static", "statutes"),
        os.path.join(os.getcwd(), "..", "lexhub-frontend", "public", "assets", "statutes")
    ]
    
    statutes_dir = None
    for p in possible_paths:
        if os.path.exists(p):
            statutes_dir = p
            break

    if not statutes_dir:
        print("Warning: Statutes directory not found. AI will function without specific context.")
        cached_context = "Note: Specific IP Law statutes are not currently loaded in the context, but I can provide general legal information."
        return cached_context

    context = ""
    try:
        pdf_files = [f for f in os.listdir(statutes_dir) if f.lower().endswith(".pdf")]
        
        for filename in pdf_files[:5]: # Limit to first 5 for performance/token limit
            try:
                path = os.path.join(statutes_dir, filename)
                reader = PdfReader(path)
                text = f"\n\n--- Start of Document: {filename} ---\n"
                # Read first 3 pages of each PDF
                for i in range(min(3, len(reader.pages))):
                    extracted = reader.pages[i].extract_text()
                    if extracted:
                        text += extracted
                context += text
            except Exception as e:
                print(f"Error reading {filename}: {e}")
    except Exception as e:
        print(f"Error listing directory: {e}")
            
    cached_context = context if context else "No statutes found in the directory."
    return cached_context

SYSTEM_PROMPT = """You are LexHub AI, a specialized Intellectual Property Law assistant for Sri Lanka.
Your goal is to provide accurate, helpful, and professional legal information.
You specialize in:
1. Intellectual Property Act, No. 36 of 2003 (Sri Lanka)
2. Trademarks, Copyrights, Patents, and Industrial Designs
3. Computer Crimes Act and Electronic Transactions Act
4. International IP treaties (WIPO, Berne Convention, etc.)

Instructions:
- Use the provided context from statutes if available.
- Always be professional.
- If a user asks in Sinhala, answer in Sinhala. If in English, answer in English.
- If you are unsure, suggest consulting a qualified legal professional.
- Mention that this information is for educational purposes for the WSO2 Ballerina 2025 Competition.
"""

@router.post("/")
async def chat_with_ai(request: ChatRequest):
    if not api_key:
        return {
            "role": "assistant",
            "content": "I'm sorry, I need a Google Gemini API Key to function. Please ensure GOOGLE_API_KEY is set in the environment variables."
        }

    try:
        # Construct context (uses cache if available)
        pdf_context = extract_pdf_context()
        
        # Initialize model
        model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=SYSTEM_PROMPT)
        
        # Format history for Gemini
        history = []
        for msg in request.history:
            role = "user" if msg.role == "user" else "model"
            history.append({"role": role, "parts": [{"text": msg.content}]})

        # Start chat
        chat = model.start_chat(history=history)
        
        # Send message with context hint
        full_query = f"Context from local statutes:\n{pdf_context}\n\nUser Question: {request.message}"
        response = chat.send_message(full_query)
        
        if not response or not response.text:
            raise Exception("Empty response from Gemini")

        return {
            "role": "assistant",
            "content": response.text
        }
    except Exception as e:
        print(f"Chat error: {str(e)}")
        # Return a user-friendly error instead of 500
        return {
            "role": "assistant",
            "content": f"I'm sorry, I encountered an error while processing your request: {str(e)}"
        }
