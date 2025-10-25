from fastapi import APIRouter, HTTPException, status, Depends
from schemas import GenreCreate
import models
from routers.rbac import get_current_user, require_role
from fastapi.security import OAuth2PasswordRequestForm
from routers.authtoken import create_access_token
from hashing import hash_password, verify_password
from database import get_db
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/genre",   
    tags=["Genre"]
    )

@router.post('/create')
def create_genre(request: GenreCreate, current_user: dict = Depends(require_role("Admin","Staff")), db: Session = Depends(get_db)):
    genre = models.Genre(name = request.name)
    db.add(genre)
    db.commit()

    return {"message": f"{genre.name} genre added with id {genre.id}"}

@router.get('/getallgenre')
def get_all_genre(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    genres = db.query(models.Genre).all()
    if not genres:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No genres at the moment")
    return {"genres": genres}

@router.get('/get/{id}')
def get_genre(id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    genre = db.query(models.Genre).filter(models.Genre.id == id).first()
    if not genre:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No genre with id {id}")
    return {"genre": genre}

@router.delete('/delete/{id}')
def delete_genre(id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    genre = db.query(models.Genre).filter(models.Genre.id == id).first()
    if not genre:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No genre with id {id}")
    db.delete(genre)
    db.commit()

    return {"message": f"Genre with id {id} deleted"}

