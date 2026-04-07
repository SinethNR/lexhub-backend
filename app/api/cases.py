import os
import shutil
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models import Case, CaseDocument, CaseNote, Consultation, User, Lawyer
from ..schemas import CaseResponse, CaseCreate, CaseDocumentResponse, CaseNoteResponse, CaseNoteCreate
from ..core.security import get_current_user
from .notifications import create_notification

router = APIRouter(prefix="/cases", tags=["cases"])

# Case documents upload directory
CASE_UPLOAD_DIR = os.path.join("app", "static", "cases")

@router.post("/", response_model=CaseResponse)
def create_case(case: CaseCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check if consultation exists and belongs to the lawyer
    consultation = db.query(Consultation).filter(Consultation.id == case.consultation_id).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")
    
    # Authorized? (Either the lawyer or the client)
    is_client = consultation.user_id == current_user.id
    lawyer_profile = db.query(Lawyer).filter(Lawyer.user_id == current_user.id).first()
    is_lawyer = lawyer_profile and consultation.lawyer_id == lawyer_profile.id
    
    if not (is_client or is_lawyer):
        raise HTTPException(status_code=403, detail="Not authorized to initiate this case workspace")
    
    if consultation.status == "pending":
        raise HTTPException(status_code=400, detail="Cannot initiate case for a pending consultation")
    
    # Already exists?
    existing_case = db.query(Case).filter(Case.consultation_id == case.consultation_id).first()
    if existing_case:
        return existing_case

    new_case = Case(
        consultation_id=case.consultation_id,
        title=case.title,
        status="active"
    )
    db.add(new_case)
    db.commit()
    db.refresh(new_case)
    return new_case

@router.get("/me", response_model=List[CaseResponse])
def get_my_cases(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.user_type in ["lawyer", "admin"]:
        lawyer_profile = db.query(Lawyer).filter(Lawyer.user_id == current_user.id).first()
        if not lawyer_profile:
            return []
        return db.query(Case).join(Consultation).filter(Consultation.lawyer_id == lawyer_profile.id).all()
    else:
        return db.query(Case).join(Consultation).filter(Consultation.user_id == current_user.id).all()

@router.get("/{case_id}", response_model=CaseResponse)
def get_case_details(case_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Verification of access...
    consultation = case.consultation
    lawyer_profile = db.query(Lawyer).filter(Lawyer.user_id == current_user.id).first()
    
    is_lawyer = lawyer_profile and consultation.lawyer_id == lawyer_profile.id
    is_client = consultation.user_id == current_user.id
    
    if not (is_lawyer or is_client or current_user.user_type == "admin"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Attach names for response
    case.lawyer_name = consultation.lawyer.user.name
    case.client_name = consultation.user.name
    
    # Attach names to docs and notes
    for doc in case.documents:
        doc.uploader_name = doc.uploader.name
    for note in case.notes:
        note.author_name = note.author.name
        
    return case

@router.post("/{case_id}/documents")
async def upload_case_document(
    case_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    if not os.path.exists(CASE_UPLOAD_DIR):
        os.makedirs(CASE_UPLOAD_DIR, exist_ok=True)
        
    # Save file
    file_extension = os.path.splitext(file.filename)[1]
    safe_filename = f"case_{case_id}_{int(datetime.utcnow().timestamp())}{file_extension}"
    file_path = os.path.join(CASE_UPLOAD_DIR, safe_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    new_doc = CaseDocument(
        case_id=case_id,
        uploader_id=current_user.id,
        file_url=f"/static/cases/{safe_filename}",
        file_name=file.filename,
        file_type=file_extension.upper().replace(".","")
    )
    db.add(new_doc)
    db.commit()
    return new_doc

@router.post("/{case_id}/notes", response_model=CaseNoteResponse)
def add_case_note(
    case_id: int,
    note: CaseNoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    new_note = CaseNote(
        case_id=case_id,
        author_id=current_user.id,
        content=note.content,
        note_type=note.note_type
    )
    db.add(new_note)
    db.commit()
    db.refresh(new_note)

    # Notify the other party
    consultation = case.consultation
    if consultation:
        target_id = consultation.lawyer.user_id if current_user.user_type == "user" else consultation.user_id
        create_notification(
            db=db,
            user_id=target_id,
            title="New Message in Workspace",
            message=f"{current_user.name} sent a new message in {case.title}",
            notif_type="new_message",
            reference_id=case_id
        )

    new_note.author_name = current_user.name
    return new_note

