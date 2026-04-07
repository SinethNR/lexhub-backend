from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..models import Consultation, User, Lawyer
from ..schemas import ConsultationCreate, ConsultationResponse
from ..core.security import get_current_user
from .notifications import create_notification

router = APIRouter(prefix="/consultations", tags=["consultations"])

@router.post("/", response_model=ConsultationResponse)
def create_consultation(consultation: ConsultationCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.user_type != "user":
        raise HTTPException(status_code=403, detail="Only standard users can book consultations")

    # Check if lawyer exists (frontend sends the User ID of the lawyer)
    lawyer = db.query(Lawyer).filter(Lawyer.user_id == consultation.lawyer_id).first()
    if not lawyer:
        raise HTTPException(status_code=404, detail="Lawyer not found")

    new_consultation = Consultation(
        user_id=current_user.id,
        lawyer_id=lawyer.id,
        consultation_date=consultation.consultation_date,
        consultation_time=consultation.consultation_time,
        description=consultation.description,
        contact_phone=consultation.contact_phone,
        contact_email=consultation.contact_email,
        is_paid=consultation.is_paid,
        status="pending"
    )
    db.add(new_consultation)
    db.commit()
    db.refresh(new_consultation)

    # Notify Lawyer
    create_notification(
        db=db,
        user_id=lawyer.user_id,
        title="New Appointment Booking",
        message=f"{current_user.name} booked an appointment for {consultation.consultation_date} at {consultation.consultation_time}",
        notif_type="appointment_booked",
        reference_id=new_consultation.id
    )

    return new_consultation

@router.get("/my-consultations", response_model=List[ConsultationResponse])
def get_my_consultations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.user_type == "user":
        return db.query(Consultation).filter(Consultation.user_id == current_user.id).all()
    elif current_user.user_type in ["lawyer", "admin"]:
        lawyer_profile = db.query(Lawyer).filter(Lawyer.user_id == current_user.id).first()
        if not lawyer_profile:
            return []
        return db.query(Consultation).filter(Consultation.lawyer_id == lawyer_profile.id).all()
    else:
        return db.query(Consultation).all() # Admins see all

@router.get("/booked-slots", response_model=List[str])
def get_booked_slots(lawyer_user_id: int, date: str, db: Session = Depends(get_db)):
    # The frontend passes the User ID of the lawyer (selectedLawyer.id)
    lawyer_profile = db.query(Lawyer).filter(Lawyer.user_id == lawyer_user_id).first()
    if not lawyer_profile:
        return []
        
    bookings = db.query(Consultation).filter(
        Consultation.lawyer_id == lawyer_profile.id,
        Consultation.consultation_date == date,
        Consultation.status.in_(["pending", "confirmed"])
    ).all()
    
    return [b.consultation_time for b in bookings]

@router.put("/{consultation_id}/status", response_model=ConsultationResponse)
def update_consultation_status(consultation_id: int, status: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found")

    if current_user.user_type == "lawyer":
        lawyer_profile = db.query(Lawyer).filter(Lawyer.user_id == current_user.id).first()
        if not lawyer_profile or consultation.lawyer_id != lawyer_profile.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this consultation")
    elif current_user.user_type == "user":
        if consultation.user_id != current_user.id or status not in ["cancelled"]:
            raise HTTPException(status_code=403, detail="Users can only cancel their own consultations")
            
    old_status = consultation.status
    consultation.status = status
    db.commit()
    db.refresh(consultation)

    # Notify user when lawyer accepts/rejects
    if current_user.user_type == "lawyer" and status in ["confirmed", "cancelled"]:
        msg = f"Your appointment on {consultation.consultation_date} has been {'confirmed' if status == 'confirmed' else 'cancelled'} by your lawyer."
        create_notification(
            db=db,
            user_id=consultation.user_id,
            title="Appointment " + ("Confirmed" if status == "confirmed" else "Cancelled"),
            message=msg,
            notif_type="appointment_status",
            reference_id=consultation.id
        )

    return consultation
