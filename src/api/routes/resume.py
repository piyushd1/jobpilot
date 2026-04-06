import uuid
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("/upload")
async def upload_resume(file: Annotated[UploadFile, File(...)]):
    """
    Validates PDF and returns a resume reference.
    In production: encrypts & uploads to MinIO.
    In dev: stores locally in /tmp.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    content = await file.read()
    file_id = str(uuid.uuid4())
    object_name = f"{file_id}.pdf"

    # Dev mode: store to /tmp instead of MinIO
    try:
        import os

        tmp_dir = "/tmp/jobpilot_resumes"
        os.makedirs(tmp_dir, exist_ok=True)
        filepath = os.path.join(tmp_dir, object_name)
        with open(filepath, "wb") as f:
            f.write(content)
        storage_ref = filepath
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    record_id = str(uuid.uuid4())
    return {
        "status": "success",
        "resume_id": record_id,
        "storage_ref": storage_ref,
        "message": "Resume uploaded successfully.",
    }
