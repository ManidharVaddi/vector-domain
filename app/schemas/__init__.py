from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class DocumentUploadResponse(BaseModel):
    filename: str
    message: str
    document_id: str

# Add at the bottom of app/schemas/__init__.py

class QuestionRequest(BaseModel):
    query: str

class DocumentList(BaseModel):
    document_id: str
    filename: str
    uploaded_at: datetime

class ConversationResponse(BaseModel):
    query: str
    answer: str
    created_at: datetime


class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    uploaded_at: datetime

class ConversationHistory(BaseModel):
    query: str
    answer: str
    created_at: datetime  
