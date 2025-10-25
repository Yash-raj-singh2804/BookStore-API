from fastapi import Depends, HTTPException, status
from routers.authtoken import verify_access_token
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_access_token(token)
    user_id = payload.get("user_id")
    role = payload.get("role")
    if user_id is None or role is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return {"user_id": user_id, "role": role}

def require_role(*roles):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        return current_user
    return role_checker