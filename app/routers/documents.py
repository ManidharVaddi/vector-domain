# app/routers/documents.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.schemas import DocumentUploadResponse, QuestionRequest, DocumentResponse, ConversationHistory
from app.services.rag_service import process_document, ask_question
from app.database import get_db
from app.models import Document, Conversation
import shutil
from pathlib import Path
import uuid

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

def get_current_user(token: str = Depends(oauth2_scheme)):
    """Extract username from token"""
    from jose import jwt, JWTError
    import os
    from dotenv import load_dotenv
    load_dotenv()
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(401, "Invalid token")
        return username
    except:
        raise HTTPException(401, "Invalid token")

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    if not file.filename.lower().endswith(('.pdf', '.txt', '.md')):
        raise HTTPException(400, detail="Only PDF, TXT, MD files allowed")
    
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
    
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        chunks = process_document(str(file_path), file.filename)
        
        doc = Document(
            filename=file.filename,
            file_path=str(file_path),
            document_id=file_id,
            user_id=1  # TODO: Link with real user_id later
        )
        db.add(doc)
        db.commit()
        
        return {
            "filename": file.filename,
            "message": f"Successfully processed {chunks} chunks",
            "document_id": file_id
        }
    except Exception as e:
        raise HTTPException(500, detail=f"Upload failed: {str(e)}")

@router.get("/list", response_model=list[DocumentResponse])
def list_documents(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    docs = db.query(Document).all()
    return docs

@router.delete("/delete/{document_id}")
def delete_document(
    document_id: str, 
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.document_id == document_id).first()
    if not doc:
        raise HTTPException(404, detail="Document not found")
    
    # Delete file from disk
    try:
        Path(doc.file_path).unlink(missing_ok=True)
    except:
        pass
    
    db.delete(doc)
    db.commit()
    return {"message": "Document deleted successfully"}

@router.post("/ask")
async def ask_document_question(
    request: QuestionRequest,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    try:
        result = ask_question(request.query)
        
        conv = Conversation(
            user_id=1,
            query=request.query,
            answer=result["answer"]
        )
        db.add(conv)
        db.commit()
        
        return {
            "query": request.query,
            "answer": result["answer"],
            "sources_found": result.get("sources_found", 0)
        }
    except Exception as e:
        raise HTTPException(500, detail="Failed to answer question")

@router.get("/history", response_model=list[ConversationHistory])
def get_history(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    history = db.query(Conversation).order_by(Conversation.created_at.desc()).limit(10).all()
    return history