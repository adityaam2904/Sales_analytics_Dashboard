import os
import hashlib
import shutil
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from fastapi import Depends
from app.database import get_db
from sqlalchemy import text

router = APIRouter(prefix="/upload", tags=["Upload"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
ALLOWED_ENTITIES = {"customers", "products", "orders"}

def compute_hash(file_path: str) -> str:
    """Compute SHA-256 hash of a file to detect duplicates."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

@router.post("/")
async def upload_file(
    entity: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Validate entity type
    if entity not in ALLOWED_ENTITIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid entity. Must be one of: {ALLOWED_ENTITIES}"
        )

    # Validate file type
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

    # Save file to uploads folder
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    stored_path = os.path.join(UPLOAD_DIR, f"{entity}_{file.filename}")

    with open(stored_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Compute file hash
    file_hash = compute_hash(stored_path)
    file_size = os.path.getsize(stored_path)

    # Check if same file was already uploaded (duplicate detection)
    existing = db.execute(text("""
        SELECT file_id, status FROM uploaded_files
        WHERE entity = :entity AND file_hash = :hash
    """), {"entity": entity, "hash": file_hash}).fetchone()

    if existing:
        os.remove(stored_path)  # Remove duplicate file
        return {
            "message": "⚠️ This file has already been uploaded.",
            "file_id": existing.file_id,
            "status": existing.status,
            "duplicate": True
        }

    # Save file record to database
    result = db.execute(text("""
        INSERT INTO uploaded_files 
            (entity, original_name, stored_path, file_hash, size_bytes, status)
        VALUES 
            (:entity, :original_name, :stored_path, :file_hash, :size_bytes, 'uploaded')
        RETURNING file_id
    """), {
        "entity": entity,
        "original_name": file.filename,
        "stored_path": stored_path,
        "file_hash": file_hash,
        "size_bytes": file_size
    })
    db.commit()

    file_id = result.fetchone().file_id

    return {
        "message": "✅ File uploaded successfully.",
        "file_id": file_id,
        "entity": entity,
        "filename": file.filename,
        "size_bytes": file_size,
        "duplicate": False
    }

@router.get("/files")
def get_uploaded_files(db: Session = Depends(get_db)):
    """Get list of all uploaded files and their status."""
    files = db.execute(text("""
        SELECT file_id, entity, original_name, size_bytes,
               status, uploaded_at, rows_read, rows_inserted,
               rows_rejected, error_message
        FROM uploaded_files
        ORDER BY uploaded_at DESC
    """)).fetchall()

    return [dict(row._mapping) for row in files]