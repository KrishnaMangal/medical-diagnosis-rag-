from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from ..auth.route import authenticate_user
from .vectorstore import load_vectorstore
import uuid
from typing import List
# from ..config.db import report_collection

router=APIRouter(prefix="/reports", tags=["reports"])
@router.post("/upload")
async def upload_report(user=Depends(authenticate_user),files: List[UploadFile] = File(...)):
    if user["role"] != "patient":
        raise HTTPException(status_code=403, detail="Only patients can upload reports")
    doc_id = str(uuid.uuid4())
    await load_vectorstore(files, uploader=user["username"], doc_id=doc_id)
    return {"message": "Report uploaded successfully", "doc_id": doc_id}

