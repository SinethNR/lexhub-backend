from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Date, DateTime, Text, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime, date, time
from .database import Base
from .database import Base
import enum

class UserType(str, enum.Enum):
    user = "user"
    lawyer = "lawyer"
    admin = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    user_type = Column(Enum(UserType), default=UserType.user)
    joined_date = Column(DateTime, default=datetime.utcnow)
    profile_picture = Column(String(1000), nullable=True)
    bio = Column(Text, nullable=True)
    occupation = Column(String(255), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)

    lawyer_details = relationship("Lawyer", back_populates="user", uselist=False)

class Lawyer(Base):
    __tablename__ = "lawyers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    phone = Column(String(50), nullable=True)
    license_number = Column(String(100), nullable=True)
    specialty = Column(String(255), nullable=True)
    cases_handled = Column(Integer, default=0)
    success_rate = Column(String(10), nullable=True)
    education = Column(String(255), nullable=True)
    hourly_rate = Column(Integer, default=20000)
    rating = Column(Float, default=4.8)
    reviews_count = Column(Integer, default=50)
    
    user = relationship("User", back_populates="lawyer_details")
    consultations = relationship("Consultation", back_populates="lawyer")
    blogs = relationship("Blog", back_populates="lawyer")
    publications = relationship("LawyerPublication", back_populates="lawyer", cascade="all, delete-orphan")

class LawyerPublication(Base):
    __tablename__ = "lawyer_publications"

    id = Column(Integer, primary_key=True, index=True)
    lawyer_id = Column(Integer, ForeignKey("lawyers.id", ondelete="CASCADE"))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    lawyer = relationship("Lawyer", back_populates="publications")

class Consultation(Base):
    __tablename__ = "consultations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    lawyer_id = Column(Integer, ForeignKey("lawyers.id"))
    status = Column(String(50), default="pending")  # pending, confirmed, completed, cancelled
    consultation_date = Column(Date, nullable=False)
    consultation_time = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    contact_phone = Column(String(50), nullable=True)
    contact_email = Column(String(100), nullable=True)
    is_paid = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="consultations")
    lawyer = relationship("Lawyer", back_populates="consultations")

class Blog(Base):
    __tablename__ = "blogs"

    id = Column(Integer, primary_key=True, index=True)
    lawyer_id = Column(Integer, ForeignKey("lawyers.id"))
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    excerpt = Column(Text, nullable=True)
    tags = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    lawyer = relationship("Lawyer", back_populates="blogs")
    likes = relationship("BlogLike", back_populates="blog", cascade="all, delete-orphan")

class BlogLike(Base):
    __tablename__ = "blog_likes"

    blog_id = Column(Integer, ForeignKey("blogs.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    blog = relationship("Blog", back_populates="likes")

class ForumPost(Base):
    __tablename__ = "forum_posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="forum_posts")
    replies = relationship("ForumReply", back_populates="post", cascade="all, delete-orphan")
    likes = relationship("ForumLike", back_populates="post", cascade="all, delete-orphan")

class ForumReply(Base):
    __tablename__ = "forum_replies"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("forum_posts.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("ForumPost", back_populates="replies")
    user = relationship("User", backref="forum_replies")

class ForumLike(Base):
    __tablename__ = "forum_likes"

    post_id = Column(Integer, ForeignKey("forum_posts.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("ForumPost", back_populates="likes")

class StatuteDocument(Base):
    __tablename__ = "statute_documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    file_url = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="uploaded_statutes")
    sections = relationship("StatuteSection", back_populates="document", cascade="all, delete-orphan")

class StatuteSection(Base):
    __tablename__ = "statute_sections"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("statute_documents.id", ondelete="CASCADE"))
    section_number = Column(String(50), nullable=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("StatuteDocument", back_populates="sections")

class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(Integer, ForeignKey("consultations.id", ondelete="CASCADE"), unique=True)
    title = Column(String(255), nullable=False)
    status = Column(String(50), default="active") # active, closed
    created_at = Column(DateTime, default=datetime.utcnow)

    consultation = relationship("Consultation", backref="case")
    documents = relationship("CaseDocument", back_populates="case", cascade="all, delete-orphan")
    notes = relationship("CaseNote", back_populates="case", cascade="all, delete-orphan")

class CaseDocument(Base):
    __tablename__ = "case_documents"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"))
    uploader_id = Column(Integer, ForeignKey("users.id"))
    file_url = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=True) # PDF, Image, etc.
    category = Column(String(50), nullable=True) # NIC, POL, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="documents")
    uploader = relationship("User")

class CaseNote(Base):
    __tablename__ = "case_notes"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"))
    author_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text, nullable=False)
    note_type = Column(String(50), default="guidance") # guidance, status_update, legal_report
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="notes")
    author = relationship("User")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(100), nullable=False)
    reference_id = Column(Integer, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="notifications")

class CaseTodo(Base):
    __tablename__ = "case_todos"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"))
    task = Column(Text, nullable=False)
    due_date = Column(Date, nullable=True)
    status = Column(String(20), default="pending") # pending, noted, done
    created_at = Column(DateTime, default=datetime.utcnow)
    case = relationship("Case", backref="todos")

class CaseReminder(Base):
    __tablename__ = "case_reminders"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"))
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    is_urgent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    case = relationship("Case", backref="reminders")

class CasePastRecord(Base):
    __tablename__ = "case_past_records"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"))
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)
    mistakes = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    case = relationship("Case", backref="past_records")

class CaseUserRequest(Base):
    __tablename__ = "case_user_requests"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id"))
    request_text = Column(Text, nullable=False)
    lawyer_reply = Column(Text, nullable=True)
    status = Column(String(50), default="pending") # pending, addressed
    created_at = Column(DateTime, default=datetime.utcnow)
    case = relationship("Case", backref="user_requests")
    user = relationship("User")
