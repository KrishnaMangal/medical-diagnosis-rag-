from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from .models import signupRequest
from .hash_utils import hash_password, verify_password
from ..config.db import users_collection


router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBasic()

def authenticate_user(credentials: HTTPBasicCredentials = Depends(security)):
    user = users_collection.find_one({"username": credentials.username})
    if user and verify_password(credentials.password, user["password"]):
        return user 
    raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/signup")
def signup(request: signupRequest):#pydantic model for request body
    existing_user = users_collection.find_one({"username": request.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_password = hash_password(request.password)
    user_data = {
        "username": request.username,
        "password": hashed_password,
        "role": request.role
    }
    users_collection.insert_one(user_data)
    return {"message": "User created successfully"}

@router.post("/login")
def login(user= Depends(authenticate_user)):
    return {"username": user['username'], "role": user["role"]}
