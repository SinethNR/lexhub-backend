from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date

class PublicationCreate(BaseModel):
    title: str
    description: Optional[str] = None

class PublicationResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class LawyerDetails(BaseModel):
    phone: Optional[str] = None
    license_number: Optional[str] = None
    specialty: Optional[str] = None
    cases_handled: Optional[int] = 0
    success_rate: Optional[str] = None
    education: Optional[str] = None
    hourly_rate: Optional[int] = 20000
    rating: Optional[float] = 4.8
    reviews_count: Optional[int] = 50
    publications: List[PublicationResponse] = []

class UserBase(BaseModel):
    name: str
    email: EmailStr
    user_type: str = "user"
    bio: Optional[str] = None
    occupation: Optional[str] = None
    linkedin_url: Optional[str] = None
    phone: Optional[str] = None

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class UserCreate(UserBase):
    password: str
    # Lawyer specific optional fields during registration
    phone: Optional[str] = None
    licenseNumber: Optional[str] = None
    specialty: Optional[str] = None

class UserProfileResponse(UserBase):
    id: int
    joined_date: datetime
    profile_picture: Optional[str] = None
    lawyer_details: Optional[LawyerDetails] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str
    user_type: str
    id: int

class ConsultationBase(BaseModel):
    lawyer_id: int
    consultation_date: date
    consultation_time: str
    description: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    is_paid: bool = False

class ConsultationCreate(ConsultationBase):
    pass

class ConsultationResponse(ConsultationBase):
    id: int
    user_id: int
    status: str
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    is_paid: bool = False
    created_at: datetime
    user: Optional[UserBase] = None
    class Config:
        from_attributes = True

class BlogBase(BaseModel):
    title: str
    content: str
    excerpt: Optional[str] = None
    tags: Optional[str] = None

class BlogCreate(BlogBase):
    pass

class BlogResponse(BlogBase):
    id: int
    lawyer_id: int
    created_at: datetime
    likes_count: int = 0
    author_name: str
    author_photo: Optional[str] = None
    has_liked: bool = False

    class Config:
        from_attributes = True

class ForumReplyResponse(BaseModel):
    id: int
    content: str
    post_id: int
    user_id: int
    created_at: datetime
    author_name: str
    author_photo: Optional[str] = None

    class Config:
        from_attributes = True

class ForumReplyCreate(BaseModel):
    content: str

class ForumPostBase(BaseModel):
    title: str
    content: str
    category: str

class ForumPostCreate(ForumPostBase):
    pass

class ForumPostResponse(ForumPostBase):
    id: int
    user_id: int
    created_at: datetime
    author_name: str
    author_photo: Optional[str] = None
    replies_count: int = 0
    likes_count: int = 0
    has_liked: bool = False
    # Use the name of the class for lazy evaluation if needed, but here we can just use the class
    replies: List[ForumReplyResponse] = []

    class Config:
        from_attributes = True

class StatuteResponse(BaseModel):
    id: int
    user_id: int
    title: str
    category: str
    description: Optional[str] = None
    file_url: str
    file_name: str
    file_size: Optional[str] = None
    created_at: datetime
    uploader_name: str

    class Config:
        from_attributes = True

class StatuteSectionResponse(BaseModel):
    id: int
    document_id: int
    section_number: Optional[str] = None
    title: str
    content: str
    summary: Optional[str] = None
    created_at: datetime
    document_title: Optional[str] = None

    class Config:
        from_attributes = True

class CaseNoteBase(BaseModel):
    content: str
    note_type: str = "guidance"

class CaseNoteCreate(CaseNoteBase):
    pass

class CaseNoteResponse(CaseNoteBase):
    id: int
    case_id: int
    author_id: int
    created_at: datetime
    author_name: Optional[str] = None

    class Config:
        from_attributes = True

class CaseDocumentResponse(BaseModel):
    id: int
    case_id: int
    uploader_id: int
    file_url: str
    file_name: str
    file_type: Optional[str] = None
    category: Optional[str] = None
    created_at: datetime
    uploader_name: Optional[str] = None

    class Config:
        from_attributes = True

class CaseResponse(BaseModel):
    id: int
    consultation_id: int
    title: str
    status: str
    created_at: datetime
    documents: List[CaseDocumentResponse] = []
    notes: List[CaseNoteResponse] = []
    lawyer_name: Optional[str] = None
    client_name: Optional[str] = None

    class Config:
        from_attributes = True

class CaseCreate(BaseModel):
    consultation_id: int
    title: str

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    type: str
    reference_id: Optional[int] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
