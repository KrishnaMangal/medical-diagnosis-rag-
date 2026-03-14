from pydantic import BaseModel

class signupRequest(BaseModel):
    username: str
    password: str
    role: str