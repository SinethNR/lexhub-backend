import os
import shutil
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Lawyer, User, LawyerPublication
from ..schemas import UserProfileResponse, LawyerDetails, PublicationResponse
from ..core.security import get_current_user

router = APIRouter(prefix="/lawyers", tags=["lawyers"])

# Define upload directory for publications
PUB_UPLOAD_DIR = os.path.join("app", "static", "publications")

@router.get("/", response_model=List[UserProfileResponse])
def get_all_lawyers(db: Session = Depends(get_db)):
    # Return all users who have set up lawyer details, including Admins
    lawyers = db.query(User).join(Lawyer, User.id == Lawyer.user_id).all()
    return lawyers

@router.get("/{lawyer_id}", response_model=UserProfileResponse)
def get_lawyer_by_id(lawyer_id: int, db: Session = Depends(get_db)):
    lawyer = db.query(User).join(Lawyer).filter(Lawyer.id == lawyer_id).first()
    if not lawyer:
        raise HTTPException(status_code=404, detail="Lawyer not found")
    return lawyer

@router.post("/publications", response_model=PublicationResponse)
async def create_publication(
    title: str = Form(...),
    description: str = Form(None),
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.user_type not in ["lawyer", "admin"]:
        raise HTTPException(status_code=403, detail="Only lawyers can add publications")
    
    lawyer = db.query(Lawyer).filter(Lawyer.user_id == current_user.id).first()
    if not lawyer:
        raise HTTPException(status_code=404, detail="Lawyer profile not found")

    image_url = None
    if image:
        if not os.path.exists(PUB_UPLOAD_DIR):
            os.makedirs(PUB_UPLOAD_DIR, exist_ok=True)
            
        safe_filename = f"{datetime.now().timestamp()}_{image.filename.replace(' ', '_')}"
        file_path = os.path.join(PUB_UPLOAD_DIR, safe_filename)
        
        try:
            image.file.seek(0)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
            image_url = f"/static/publications/{safe_filename}"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save image: {str(e)}")

    pub = LawyerPublication(
        lawyer_id=lawyer.id,
        title=title,
        description=description,
        image_url=image_url
    )
    db.add(pub)
    db.commit()
    db.refresh(pub)
    return pub

@router.delete("/publications/{pub_id}")
def delete_publication(
    pub_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.user_type not in ["lawyer", "admin"]:
        raise HTTPException(status_code=403, detail="Only lawyers can delete publications")
        
    lawyer = db.query(Lawyer).filter(Lawyer.user_id == current_user.id).first()
    pub = db.query(LawyerPublication).filter(LawyerPublication.id == pub_id, LawyerPublication.lawyer_id == lawyer.id).first()
    
    if not pub:
        raise HTTPException(status_code=404, detail="Publication not found or unauthorized")
        
    if pub.image_url:
        filename = pub.image_url.split("/")[-1]
        file_path = os.path.join(PUB_UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            
    db.delete(pub)
    db.commit()
    return {"message": "Publication deleted"}
