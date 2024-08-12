from fastapi import HTTPException
from fastapi_auth_466.user import User

def register(user: User, db):
    if db.get_user(username=user.username) is not None:
        raise HTTPException(status_code=400, detail="Username already exists")
    # Implement user creation here...
