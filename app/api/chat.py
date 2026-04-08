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

import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache for statutory knowledge
class KnowledgeManager:
    def __init__(self):
        self.documents = [] # List of {title, sections: [{title, content}]}
        self.is_indexed = False

    def refresh(self):
        """Re-index all PDFs in the statutes directory."""
        logger.info("Refreshing AI Knowledge Base...")
        possible_paths = [
            os.path.join(os.getcwd(), "app", "static", "statutes"),
            r"E:\Software Projects Sineth\WSO2 Ballerina 2025 Competition\lexhub-frontend\public\assets\statutes"
        ]
        
        statutes_dir = next((p for p in possible_paths if os.path.exists(p)), None)
        if not statutes_dir:
            logger.warning("Statutes directory not found.")
            return

        new_documents = []
        try:
            pdf_files = [f for f in os.listdir(statutes_dir) if f.lower().endswith(".pdf")]
            for filename in pdf_files:
                try:
                    path = os.path.join(statutes_dir, filename)
                    reader = PdfReader(path)
                    doc_content = {"title": filename, "chunks": []}
                    
                    # Extract text and split into manageable chunks (approx 1000 characters)
                    full_text = ""
                    for page in reader.pages:
                        text = page.extract_text()
                        if text: full_text += text + "\n"
                    
                    # Basic chunking by paragraphs or double newlines
                    paragraphs = re.split(r'\n\s*\n', full_text)
                    for i, p in enumerate(paragraphs):
                        if len(p.strip()) > 50:
                            doc_content["chunks"].append({
                                "id": i,
                                "text": p.strip()[:2000] # Limit chunk size
                            })
                    new_documents.append(doc_content)
                except Exception as e:
                    logger.error(f"Error indexing {filename}: {e}")
            
            self.documents = new_documents
            self.is_indexed = True
            logger.info(f"AI Knowledge Base updated with {len(new_documents)} documents.")
        except Exception as e:
            logger.error(f"Knowledge refresh error: {e}")

    def get_relevant_context(self, query: str, limit: int = 5):
        """Perform a keyword-based search to find relevant context for the query."""
        if not self.is_indexed:
            self.refresh()
            
        keywords = re.findall(r'\w+', query.lower())
        relevant_chunks = []
        
        for doc in self.documents:
            for chunk in doc["chunks"]:
                score = sum(1 for k in keywords if k in chunk["text"].lower())
                if score > 0:
                    relevant_chunks.append({
                        "title": doc["title"],
                        "text": chunk["text"],
                        "score": score
                    })
        
        # Sort by score and take top N
        relevant_chunks.sort(key=lambda x: x["score"], reverse=True)
        
        context = ""
        for item in relevant_chunks[:limit]:
            context += f"\n[Source: {item['title']}]\n{item['text']}\n"
            
        return context if context else "No specific statutory context found for this query."

# Global instance
knowledge_manager = KnowledgeManager()

SYSTEM_PROMPT = """You are LexHub AI, the official Intellectual Property Law Assistant for Sri Lanka.
Your goal is to provide highly accurate, professional, and cited legal information.

PRIMARY DIRECTIVE:
1. When a user asks a question, first check the "LOCAL STATUTES" context provided below.
2. If the answer is found in the local statutes, cite the source document clearly (e.g., "According to the [Document Name]...").
3. If the answer is NOT in the local statutes, provide a response based on your general legal training, but add a disclaimer that the specific local statute was not found in the current knowledge base.
4. Always maintain a professional, helpful, and formal tone.
5. Answer in the same language as the user (Sinhala, English, or Tamil).

SPECIALIZATION:
- Intellectual Property Act, No. 36 of 2003
- Trademarks, Patents, Copyrights, Industrial Designs
- Computer Crimes & Electronic Transactions
- WIPO treaties as applied in Sri Lanka

DISCLAIMER: This information is for educational purposes for the WSO2 Ballerina 2025 Competition and should not be considered professional legal advice.
"""

@router.post("/")
async def chat_with_ai(request: ChatRequest):
    if not api_key:
        return {
            "role": "assistant",
            "content": "I'm sorry, I need a Google Gemini API Key. Please add GOOGLE_API_KEY to Render Environment Variables."
        }

    try:
        # Perform intelligent context retrieval
        context = knowledge_manager.get_relevant_context(request.message)
        
        # Initialize model
        model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=SYSTEM_PROMPT)
        
        # Format history
        history = []
        for msg in request.history:
            role = "user" if msg.role == "user" else "model"
            history.append({"role": role, "parts": [{"text": msg.content}]})

        # Start chat
        chat = model.start_chat(history=history)
        
        # Construct final prompt with retrieved context
        final_prompt = f"### LOCAL STATUTES CONTEXT:\n{context}\n\n### USER QUESTION:\n{request.message}"
        
        response = chat.send_message(final_prompt)
        
        if not response or not response.text:
            raise Exception("Gemini returned an empty response.")

        return {
            "role": "assistant",
            "content": response.text
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {
            "role": "assistant",
            "content": f"I'm sorry, I encountered an error: {str(e)}"
        }
