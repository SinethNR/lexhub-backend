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

def extract_pdf_context():
    """Extract context from statutes PDF files."""
    # Note: Using absolute path to frontend's public/assets/statutes for the competition environment
    statutes_dir = r"E:\Software Projects Sineth\WSO2 Ballerina 2025 Competition\lexhub-frontend\public\assets\statutes"
    context = ""
    
    if not os.path.exists(statutes_dir):
        return "Note: IP Law statutes are available in the system."

    pdf_files = [f for f in os.listdir(statutes_dir) if f.lower().endswith(".pdf")]
    
    for filename in pdf_files[:5]: # Limit to first 5 for performance/token limit
        try:
            path = os.path.join(statutes_dir, filename)
            reader = PdfReader(path)
            text = f"\n\n--- Start of Document: {filename} ---\n"
            # Read first 3 pages of each PDF as a summary/context
            for i in range(min(3, len(reader.pages))):
                extracted = reader.pages[i].extract_text()
                if extracted:
                    text += extracted
            context += text
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            
    return context

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
            "content": "I'm sorry, I need a Google Gemini API Key to function. Please get one from Google AI Studio and add it to the environment variables."
        }

    try:
        # Construct context
        pdf_context = extract_pdf_context()
        
        # Initialize model
        model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=SYSTEM_PROMPT)
        
        # Format history for Gemini
        # (Gemini 1.5 format is different but simple chat works well)
        history = []
        for msg in request.history:
            role = "user" if msg.role == "user" else "model"
            history.append({"role": role, "parts": [msg.content]})

        # Start chat
        chat = model.start_chat(history=history)
        
        # Send message with context hint
        full_query = f"Context from local statutes:\n{pdf_context}\n\nUser Question: {request.message}"
        response = chat.send_message(full_query)
        
        return {
            "role": "assistant",
            "content": response.text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
