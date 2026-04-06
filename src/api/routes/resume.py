from fastapi import APIRouter, UploadFile, File, HTTPException
import uuid
from src.services.storage import MinioStorage

router = APIRouter(prefix="/resumes", tags=["resumes"])
storage_service = MinioStorage()

@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    """
    Validates PDF, encrypts & uploads to MinIO.
    Returns the storage reference.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    content = await file.read()
    
    # Generate unique ID for the file
    file_id = str(uuid.uuid4())
    object_name = f"{file_id}.pdf"

    try:
        storage_ref = storage_service.upload_file(content, object_name)
        # Mocking creation of a resumes DB record:
        record_id = str(uuid.uuid4())
        return {
            "status": "success",
            "resume_id": record_id,
            "storage_ref": storage_ref,
            "message": "Resume uploaded securely."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
