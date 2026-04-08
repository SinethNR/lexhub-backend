import csv
import io
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from typing import List, Dict

from ..database import get_db
from ..models import Consultation, User, Lawyer
from ..core.security import get_current_user

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/summary")
def get_report_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Basic summary counts
    if current_user.user_type in ["lawyer", "admin"]:
        lawyer_profile = db.query(Lawyer).filter(Lawyer.user_id == current_user.id).first()
        if not lawyer_profile:
            return {"total": 0, "confirmed": 0, "completed": 0, "total_earned": 0}
        
        base_query = db.query(Consultation).filter(Consultation.lawyer_id == lawyer_profile.id)
        total = base_query.count()
        confirmed = base_query.filter(Consultation.status == "confirmed").count()
        completed = base_query.filter(Consultation.status == "completed").count()
        
        # Estimate earnings
        total_earned = completed * lawyer_profile.hourly_rate
        
        # Data for chart (Last 6 months)
        chart_data = []
        for i in range(5, -1, -1):
            month_date = datetime.utcnow() - timedelta(days=i*30)
            month_name = month_date.strftime("%b")
            month_num = month_date.month
            year_num = month_date.year
            
            count = base_query.filter(
                extract('month', Consultation.created_at) == month_num,
                extract('year', Consultation.created_at) == year_num
            ).count()
            
            chart_data.append({"name": month_name, "value": count})
            
        return {
            "total": total,
            "confirmed": confirmed,
            "completed": completed,
            "total_earned": total_earned,
            "chart_data": chart_data
        }
    else:
        # For standard User
        base_query = db.query(Consultation).filter(Consultation.user_id == current_user.id)
        total = base_query.count()
        confirmed = base_query.filter(Consultation.status == "confirmed").count()
        completed = base_query.filter(Consultation.status == "completed").count()
        
        # Estimate spending (approximate since we don't store historical rate on consultation)
        total_spent = db.query(func.sum(Lawyer.hourly_rate)).join(Consultation, Consultation.lawyer_id == Lawyer.id).filter(Consultation.user_id == current_user.id, Consultation.status == "completed").scalar() or 0
        
        # Data for chart
        chart_data = []
        for i in range(5, -1, -1):
            month_date = datetime.utcnow() - timedelta(days=i*30)
            month_name = month_date.strftime("%b")
            month_num = month_date.month
            year_num = month_date.year
            
            count = base_query.filter(
                extract('month', Consultation.created_at) == month_num,
                extract('year', Consultation.created_at) == year_num
            ).count()
            
            chart_data.append({"name": month_name, "value": count})

        return {
            "total": total,
            "confirmed": confirmed,
            "completed": completed,
            "total_spent": total_spent,
            "chart_data": chart_data
        }

@router.get("/export")
def export_report_csv(
    range_type: str = Query("monthly", pattern="^(weekly|monthly|yearly)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Calculate date threshold
    now = datetime.utcnow()
    if range_type == "weekly":
        threshold = now - timedelta(days=7)
    elif range_type == "monthly":
        threshold = now - timedelta(days=30)
    else:
        threshold = now - timedelta(days=365)
    
    # Fetch data
    if current_user.user_type in ["lawyer", "admin"]:
        lawyer_profile = db.query(Lawyer).filter(Lawyer.user_id == current_user.id).first()
        consultations = db.query(Consultation).filter(
            Consultation.lawyer_id == lawyer_profile.id,
            Consultation.created_at >= threshold
        ).all()
        header = ["Date", "Client Name", "Email", "Time", "Status", "Is Paid", "Reference ID"]
    else:
        consultations = db.query(Consultation).filter(
            Consultation.user_id == current_user.id,
            Consultation.created_at >= threshold
        ).all()
        header = ["Date", "Lawyer Name", "Time", "Status", "Is Paid", "Reference ID"]
    
    # Create CSV
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=header)
    writer.writeheader()
    
    for c in consultations:
        if current_user.user_type in ["lawyer", "admin"]:
            row = {
                "Date": c.consultation_date.strftime("%Y-%m-%d"),
                "Client Name": c.user.name,
                "Email": c.contact_email,
                "Time": c.consultation_time,
                "Status": c.status,
                "Is Paid": "Yes" if c.is_paid else "No",
                "Reference ID": f"LH-C-{c.id}"
            }
        else:
            row = {
                "Date": c.consultation_date.strftime("%Y-%m-%d"),
                "Lawyer Name": c.lawyer.user.name if c.lawyer and c.lawyer.user else "N/A",
                "Time": c.consultation_time,
                "Status": c.status,
                "Is Paid": "Yes" if c.is_paid else "No",
                "Reference ID": f"LH-C-{c.id}"
            }
        writer.writerow(row)
    
    output.seek(0)
    filename = f"LexHub_Report_{range_type}_{datetime.now().strftime('%Y%m%d')}.csv"
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
