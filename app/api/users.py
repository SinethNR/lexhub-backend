import os
import shutil
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models import User, Lawyer
from ..schemas import UserProfileResponse, UserBase, PasswordChangeRequest
from ..core.security import get_current_user, verify_password, get_password_hash

router = APIRouter(prefix="/users", tags=["users"])

# Profile picture upload directory
PROFILE_UPLOAD_DIR = os.path.join("app", "static", "profiles")

@router.post("/profile-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not os.path.exists(PROFILE_UPLOAD_DIR):
        os.makedirs(PROFILE_UPLOAD_DIR, exist_ok=True)
    
    # Save file
    file_extension = os.path.splitext(file.filename)[1]
    safe_filename = f"user_{current_user.id}_{int(datetime.utcnow().timestamp())}{file_extension}"
    file_path = os.path.join(PROFILE_UPLOAD_DIR, safe_filename)
    
    try:
        # Use file.file.seek(0) just in case
        file.file.seek(0)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Update user profile
        image_url = f"/static/profiles/{safe_filename}"
        current_user.profile_picture = image_url
        db.commit()
        return {"profile_picture": image_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save image: {str(e)}")

@router.get("/profiles", response_model=List[UserProfileResponse])
def get_profiles(user_type: Optional[str] = "all", db: Session = Depends(get_db)):
    if user_type == "all":
        users = db.query(User).all()
    else:
        users = db.query(User).filter(User.user_type == user_type).all()
    return users

@router.get("/current", response_model=UserProfileResponse)
def get_current_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/profile/{user_id}", response_model=UserProfileResponse)
def get_profile_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/profile/{user_id}")
def update_profile(user_id: int, profile_update: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.id != user_id and current_user.user_type != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to update this profile")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if "name" in profile_update:
        user.name = profile_update["name"]
    if "bio" in profile_update:
        user.bio = profile_update["bio"]
    if "profile_picture" in profile_update:
        user.profile_picture = profile_update["profile_picture"]
    if "occupation" in profile_update:
        user.occupation = profile_update["occupation"]
    if "linkedin_url" in profile_update:
        user.linkedin_url = profile_update["linkedin_url"]
    if "phone" in profile_update:
        user.phone = profile_update["phone"]
    
    lawyer_details = profile_update.get("lawyer_details", None)
    if user.user_type in ["lawyer", "admin"] and lawyer_details:
        lawyer = db.query(Lawyer).filter(Lawyer.user_id == user.id).first()
        if lawyer:
            lawyer.phone = lawyer_details.get("phone", lawyer.phone)
            lawyer.specialty = lawyer_details.get("specialty", lawyer.specialty)
            lawyer.license_number = lawyer_details.get("license_number", lawyer.license_number)
            if "hourly_rate" in lawyer_details:
                lawyer.hourly_rate = lawyer_details["hourly_rate"]
            if "cases_handled" in lawyer_details:
                lawyer.cases_handled = lawyer_details["cases_handled"]
            if "success_rate" in lawyer_details:
                lawyer.success_rate = lawyer_details["success_rate"]
            if "education" in lawyer_details:
                lawyer.education = lawyer_details["education"]
            
    db.commit()
    return {"message": "Profile updated successfully"}

@router.put("/change-password")
def change_password(request: PasswordChangeRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    
    current_user.hashed_password = get_password_hash(request.new_password)
    db.commit()
    return {"message": "Password changed successfully"}

@router.get("/demo/profiles")
def get_demo_profiles():
    # Retaining the demo data endpoint from the Ballerina source
    return [
        {
            "id": 1,
            "name": "John Doe",
            "email": "john@example.com",
            "user_type": "user",
            "joined_date": "2023-01-15",
            "profile_picture": "/images/avatars/avatar_1.jpg",
            "bio": "Regular user interested in legal assistance"
        },
        {
            "id": 2,
            "name": "Jane Smith",
            "email": "jane@lexhub.com",
            "user_type": "lawyer",
            "joined_date": "2022-11-05",
            "profile_picture": "/images/avatars/avatar_2.jpg",
            "bio": "Experienced corporate lawyer with 10 years of practice"
        }
    ]
