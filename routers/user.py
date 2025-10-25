from fastapi import APIRouter, HTTPException, status, Depends
from schemas import User, LoginRequest, UserUpdate
import models
from datetime import datetime, timedelta
from utils.send_verification import send_verification_email
import uuid
from fastapi.responses import HTMLResponse
from routers.rbac import get_current_user, require_role
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_mail import FastMail, MessageSchema, MessageType
from config import settings, conf
from routers.authtoken import create_access_token
from hashing import hash_password, verify_password
from database import get_db
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/user",   
    tags=["User"]
    )

@router.post("/register")
async def register_user(request: User, db: Session = Depends(get_db)):

    existing_user = db.query(models.User).filter(models.User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    pending_user = db.query(models.PendingRegistration).filter(models.PendingRegistration.email == request.email).first()
    if pending_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A verification email has already been sent to this address")

    token_str = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=24)

    pending = models.PendingRegistration(
        name=request.name,
        email=request.email,
        password=hash_password(request.password),
        role=request.role,
        token_hash=token_str,
        expires_at=expires_at
    )
    db.add(pending)
    db.commit()

    await send_verification_email(request.email, token_str)

    return {"message": "Registration initiated. Please check your email to verify your account."}

@router.get("/verify/{token}", response_class=HTMLResponse)
async def verify_user(token: str, db: Session = Depends(get_db)):
    pending = db.query(models.PendingRegistration).filter(models.PendingRegistration.token_hash == token).first()
    if not pending:
        return HTMLResponse("<h3>Invalid or already used verification link.</h3>", status_code=400)

    if pending.expires_at < datetime.utcnow():
        db.delete(pending)
        db.commit()
        return HTMLResponse("<h3>Link expired. Please register again.</h3>", status_code=400)
    
    new_user = models.User(
        name=pending.name,
        email=pending.email,
        password=pending.password,
        role=pending.role,
        is_verified=True
    )
    db.add(new_user)
    db.delete(pending) 
    db.commit()

    return HTMLResponse("<h2>Email verified successfully! You can now log in.</h2>")

@router.post("/login")
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email not registered")
    if not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")

    token = create_access_token({"user_id": user.id, "role": user.role})
    return {"access_token": token, "token_type": "bearer"}

@router.get('/all')
def get_all_user(db: Session = Depends(get_db), current_user: dict = Depends(require_role("Admin"))):
    users = db.query(models.User).all()
    if not users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No current users")
    return users

@router.patch('/update/{id}')
def update_user(id: int,request: UserUpdate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    new_user = db.query(models.User).filter(models.User.id == id).first()
    if not new_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with {id} not found")
    
    update_data = request.dict(exclude_unset=True)

    for key, value in update_data.items():
        if key == "password":
            value = hash_password(value)   
        setattr(new_user, key, value)

    db.commit()        
    db.refresh(new_user)

    return new_user

@router.get('/{id}')
def get_one_user(id: int, db: Session = Depends(get_db), current_user: dict = Depends(require_role("Admin","Staff"))):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with {id} not found")

    return user

@router.delete('/delete/{id}')
def delete_user(id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    book = db.query(models.User).filter(models.User.id == id).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No user with id {id}")
    
    db.delete(book)
    db.commit()

    return book
