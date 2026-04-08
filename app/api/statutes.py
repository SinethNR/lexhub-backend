import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from ..database import get_db
from ..models import StatuteDocument, StatuteSection, User, UserType
from ..schemas import StatuteResponse, StatuteSectionResponse
from ..core.security import get_current_user

router = APIRouter(prefix="/statutes", tags=["statutes"])

# Define upload directory
UPLOAD_DIR = os.path.join("app", "static", "statutes")

@router.post("/upload", response_model=StatuteResponse)
async def upload_statute(
    title: str = Form(...),
    category: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Authorization check: only lawyers and admins can upload
    if current_user.user_type not in [UserType.lawyer, UserType.admin]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only lawyers can upload statutes")

    # File type check
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are allowed")

    # Ensure directory exists
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Sanitize filename (basic)
    safe_filename = f"{datetime.now().timestamp()}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    # Save the file using streaming for reliability
    try:
        # Reset file pointer to beginning just in case
        file.file.seek(0)
        
        # Write to file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Get actual saved file size
        size_bytes = os.path.getsize(file_path)
        
        # Validation: check if file is too small (e.g., just an error page)
        # 1024 bytes is a safe threshold for a real PDF vs an HTML error page
        if size_bytes < 1024:
            # Check if it contains HTML (common for error responses from dev servers)
            file.file.seek(0)
            prefix = await file.read(100)
            if b"<!doctype" in prefix.lower() or b"<html" in prefix.lower():
                os.remove(file_path)
                raise HTTPException(
                    status_code=400, 
                    detail="Corrupted file received (HTML encountered instead of PDF). This usually happens if the upload request is intercepted by a development proxy or server error."
                )

        if size_bytes < 1024:
            file_size = f"{size_bytes} Bytes"
        elif size_bytes < 1024 * 1024:
            file_size = f"{size_bytes / 1024:.1f} KB"
        else:
            file_size = f"{size_bytes / (1024 * 1024):.1f} MB"

    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=f"File save error: {str(e)}")

    # Create DB entry
    db_statute = StatuteDocument(
        user_id=current_user.id,
        title=title,
        category=category,
        description=description,
        file_url=f"/static/statutes/{safe_filename}",
        file_name=file.filename,
        file_size=file_size
    )
    db.add(db_statute)
    db.commit()
    db.refresh(db_statute)

    # Create response with uploader name
    response_data = db_statute.__dict__.copy()
    response_data["uploader_name"] = current_user.name
    return response_data

@router.get("/", response_model=List[StatuteResponse])
def get_statutes(db: Session = Depends(get_db)):
    statutes = db.query(StatuteDocument).order_by(StatuteDocument.created_at.desc()).all()
    
    response = []
    for s in statutes:
        s_dict = s.__dict__.copy()
        s_dict["uploader_name"] = s.user.name if s.user else "System"
        response.append(s_dict)
    
    return response

@router.delete("/{id}")
def delete_statute(
    id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    statute = db.query(StatuteDocument).filter(StatuteDocument.id == id).first()
    if not statute:
        raise HTTPException(status_code=404, detail="Statute not found")
    
    # Check ownership
    if statute.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own uploads")

    # Delete physical file
    filename = statute.file_url.split("/")[-1]
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(statute)
    db.commit()
    return {"message": "Statute deleted successfully"}

@router.get("/my-uploads", response_model=List[StatuteResponse])
def get_my_uploads(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    statutes = db.query(StatuteDocument).filter(StatuteDocument.user_id == current_user.id).all()
    
    response = []
    for s in statutes:
        s_dict = s.__dict__.copy()
        s_dict["uploader_name"] = current_user.name
        response.append(s_dict)
    
    return response

@router.get("/search", response_model=List[StatuteSectionResponse])
def search_statute_sections(q: str = "", category: str = "all", db: Session = Depends(get_db)):
    query = db.query(StatuteSection).join(StatuteDocument)
    
    if q:
        search_filter = (
            StatuteSection.title.ilike(f"%{q}%") | 
            StatuteSection.content.ilike(f"%{q}%") |
            StatuteSection.section_number.ilike(f"%{q}%")
        )
        query = query.filter(search_filter)
        
    if category != "all":
        query = query.filter(StatuteDocument.category == category)
        
    sections = query.limit(50).all()
    
    response = []
    for s in sections:
        s_dict = s.__dict__.copy()
        s_dict["document_title"] = s.document.title
        response.append(s_dict)
    
    return response

@router.get("/{doc_id}/sections", response_model=List[StatuteSectionResponse])
def get_document_sections(doc_id: int, db: Session = Depends(get_db)):
    sections = db.query(StatuteSection).filter(StatuteSection.document_id == doc_id).all()
    
    response = []
    for s in sections:
        s_dict = s.__dict__.copy()
        s_dict["document_title"] = s.document.title
        response.append(s_dict)
    
    return response
