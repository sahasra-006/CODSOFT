import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.models import UploadedPDF
from backend.schemas import PDFOut
from backend.pdf_engine import clear_pdf_cache, load_pdf_into_cache

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload-pdf", response_model=PDFOut)
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Sanitize filename
    safe_name = os.path.basename(file.filename)
    filepath = os.path.join(UPLOAD_DIR, safe_name)
    
    # Handle duplicate filenames
    base, ext = os.path.splitext(safe_name)
    counter = 1
    while os.path.exists(filepath):
        safe_name = f"{base}_{counter}{ext}"
        filepath = os.path.join(UPLOAD_DIR, safe_name)
        counter += 1
    
    # Save file
    try:
        with open(filepath, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")
    
    # Save to database
    pdf = UploadedPDF(filename=safe_name, filepath=filepath)
    db.add(pdf)
    db.commit()
    db.refresh(pdf)
    
    # Pre-load into cache
    try:
        load_pdf_into_cache(pdf.id, filepath)
    except Exception:
        pass  # Non-fatal, will load on demand
    
    return pdf


@router.get("/pdfs", response_model=List[PDFOut])
def get_pdfs(db: Session = Depends(get_db)):
    return db.query(UploadedPDF).order_by(UploadedPDF.uploaded_at.desc()).all()


@router.post("/activate-pdf/{pdf_id}", response_model=PDFOut)
def activate_pdf(pdf_id: int, db: Session = Depends(get_db)):
    # Deactivate all PDFs
    db.query(UploadedPDF).update({"is_active": False})
    
    # Activate the selected one
    pdf = db.query(UploadedPDF).filter(UploadedPDF.id == pdf_id).first()
    if not pdf:
        raise HTTPException(status_code=404, detail="PDF not found")
    
    if not os.path.exists(pdf.filepath):
        raise HTTPException(status_code=404, detail="PDF file not found on disk")
    
    pdf.is_active = True
    db.commit()
    db.refresh(pdf)
    
    # Ensure it's in cache
    try:
        load_pdf_into_cache(pdf.id, pdf.filepath)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {e}")
    
    return pdf


@router.post("/deactivate-pdf")
def deactivate_pdf(db: Session = Depends(get_db)):
    db.query(UploadedPDF).update({"is_active": False})
    db.commit()
    return {"detail": "All PDFs deactivated"}


@router.delete("/pdf/{pdf_id}")
def delete_pdf(pdf_id: int, db: Session = Depends(get_db)):
    pdf = db.query(UploadedPDF).filter(UploadedPDF.id == pdf_id).first()
    if not pdf:
        raise HTTPException(status_code=404, detail="PDF not found")
    
    # Remove file
    if os.path.exists(pdf.filepath):
        try:
            os.remove(pdf.filepath)
        except Exception:
            pass
    
    # Remove from cache
    clear_pdf_cache(pdf_id)
    
    db.delete(pdf)
    db.commit()
    return {"detail": "PDF deleted"}
