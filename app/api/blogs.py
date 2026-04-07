from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, func
from typing import List, Optional

from ..database import get_db
from ..models import Blog, BlogLike, Lawyer, User
from ..schemas import BlogCreate, BlogResponse
from ..core.security import get_current_user
from .notifications import create_notification

router = APIRouter(prefix="/blogs", tags=["blogs"])

def build_blog_response(db: Session, db_blog: Blog, current_user: Optional[User] = None):
    likes_count = db.query(BlogLike).filter(BlogLike.blog_id == db_blog.id).count()
    has_liked = False
    if current_user:
        existing_like = db.query(BlogLike).filter(BlogLike.blog_id == db_blog.id, BlogLike.user_id == current_user.id).first()
        has_liked = existing_like is not None

    author_user = db_blog.lawyer.user
    
    return BlogResponse(
        id=db_blog.id,
        lawyer_id=db_blog.lawyer_id,
        title=db_blog.title,
        content=db_blog.content,
        excerpt=db_blog.excerpt,
        tags=db_blog.tags,
        created_at=db_blog.created_at,
        likes_count=likes_count,
        author_name=author_user.name,
        author_photo=author_user.profile_picture,
        has_liked=has_liked
    )

@router.get("/", response_model=List[BlogResponse])
def get_all_blogs(db: Session = Depends(get_db)):
    blogs = db.query(Blog).order_by(Blog.created_at.desc()).all()
    # We aren't strictly requiring current logged-in user to view blogs here,
    # but has_liked will be False for guests.
    # To support has_liked correctly, frontend must pass token if logged in.
    return [build_blog_response(db, b) for b in blogs]

@router.get("/me", response_model=List[BlogResponse])
def get_my_blogs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.user_type not in ["lawyer", "admin"]:
        raise HTTPException(status_code=403, detail="Only lawyers have personal blogs")
        
    lawyer = db.query(Lawyer).filter(Lawyer.user_id == current_user.id).first()
    if not lawyer:
        return []

    blogs = db.query(Blog).filter(Blog.lawyer_id == lawyer.id).order_by(Blog.created_at.desc()).all()
    return [build_blog_response(db, b, current_user) for b in blogs]

@router.post("/", response_model=BlogResponse)
def create_blog(blog: BlogCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.user_type not in ["lawyer", "admin"]:
        raise HTTPException(status_code=403, detail="Only lawyers can publish blogs")

    lawyer = db.query(Lawyer).filter(Lawyer.user_id == current_user.id).first()
    if not lawyer:
        raise HTTPException(status_code=404, detail="Lawyer profile not found")

    new_blog = Blog(
        lawyer_id=lawyer.id,
        title=blog.title,
        content=blog.content,
        excerpt=blog.excerpt,
        tags=blog.tags
    )
    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)
    
    return build_blog_response(db, new_blog, current_user)

@router.post("/{blog_id}/like")
def toggle_blog_like(blog_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")

    existing_like = db.query(BlogLike).filter(BlogLike.blog_id == blog_id, BlogLike.user_id == current_user.id).first()
    
    if existing_like:
        # Unlike
        db.delete(existing_like)
        db.commit()
        return {"action": "unliked"}
    else:
        # Like
        new_like = BlogLike(blog_id=blog_id, user_id=current_user.id)
        db.add(new_like)
        db.commit()
        # Notify the blog author - explicitly load lawyer to avoid lazy-load issues
        from ..models import Lawyer as LawyerModel
        lawyer = db.query(LawyerModel).filter(LawyerModel.id == blog.lawyer_id).first()
        if lawyer and lawyer.user_id != current_user.id:
            create_notification(
                db=db,
                user_id=lawyer.user_id,
                title="New Reaction on Your Blog",
                message=f"{current_user.name} liked your blog: '{blog.title}'",
                notif_type="blog_reaction",
                reference_id=blog_id
            )
        return {"action": "liked"}

