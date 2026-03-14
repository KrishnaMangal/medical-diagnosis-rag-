from fastapi import APIRouter, Depends, Form, HTTPException
from ..auth.route import authenticate_user
from .query import diagnosis_report
from ..config.db import report_collection, diagnosis_collection
import time

router = APIRouter(prefix="/diagnosis", tags=["diagnosis"])
@router.post("/from_report")
async def diagnosis(
    user = Depends(authenticate_user),
    doc_id: str = Form(...),
    question: str = Form(default="Please provide a diagnosis based on my report")
):
    report = report_collection.find_one({"doc_id": doc_id})

    if not report:
      raise HTTPException(status_code=404, detail="Report not found")

    # patient can only access
    if user["role"] == "patient" and report["uploader"] != user["username"]:
        raise HTTPException(status_code=406, detail="you can only access your own reports")
    # if user is not a patient , want his report for diagnosis
    if user["role"] =="patient":
        res = await diagnosis_report(user["username"], doc_id, question)

        # persist the diagnosis report
        diagnosis_collection.insert_one({
            "doc_id": doc_id,
            "requester": user["username"],
            "question": question,
            "answer": res.get("diagnosis"),
            "sources": res.get("sources", []),
            "timestamp": time.time()
        })
        return res
    # if user is doctor or admin, they can not ask diagnosis
    if user["role"] in ["doctor", "admin"]:
        raise HTTPException(status_code=406, detail="Only patients can request diagnosis with this endpoint")
    #safty check 
    raise HTTPException(status_code=408, detail="Unauthorized access")

@router.get("/by_patient_name")
async def get_patient_diagnosis(
    patient_name: str,
    user = Depends(authenticate_user)
):
    # Only doctors can view a patient's diagnosis
    if user["role"] != "doctor":
        raise HTTPException(
            status_code=403,
            detail="Only doctors can access this endpoint"
        )

    diagnosis_records = diagnosis_collection.find(
        {"requester": patient_name}
    )

    if not diagnosis_records:
        raise HTTPException(
            status_code=404,
            detail="No diagnosis found for this patient"
        )
    # Convert cursor to a list of dictionaries
    records_list = []

    for record in diagnosis_records:
        record["_id"] = str(record["_id"])  # Convert ObjectId to string for JSON serialization
        records_list.append(record)

    return records_list


    