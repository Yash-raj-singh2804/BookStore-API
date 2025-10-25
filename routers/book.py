from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
import csv, requests, random
from schemas import Book, BookOut
from typing import List
import models
from routers.rbac import get_current_user, require_role
from fastapi.security import OAuth2PasswordRequestForm
from database import get_db
from sqlalchemy import or_
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/book",   
    tags=["Books"]
    )

@router.get('/get/allbooks', response_model=List[BookOut])
def all_books(db: Session = Depends(get_db), 
            search: str = None,
            genre_id: int = None,
            min_price: int = None,
            max_price: int = None,
            is_available: bool = True,
            sort_by: str = "title",
            sort_order: str = "asc",
            skip: int = 0,
            limit: int = 10
            ):
    query = db.query(models.Book)

    if search:
        query = query.filter(
            or_(
                models.Book.title.ilike(f"%{search}%"),
                models.Book.author.ilike(f"%{search}%")
            )
        )

    if genre_id:
        query = query.filter(models.Book.genre_id == genre_id)
    if min_price:
        query = query.filter(models.Book.price >= min_price)
    if max_price:
        query = query.filter(models.Book.price <= max_price)

    sort_column = getattr(models.Book, sort_by, models.Book.title)
    if sort_order == "desc":
        sort_column = sort_column.desc()
    query = query.order_by(sort_column)

    query = query.offset(skip).limit(limit)

    books = query.all()

    if not books:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No books available")
    return books

@router.post('/create')
def create_book(request: Book, db: Session = Depends(get_db), current_user: dict = Depends(require_role("Admin","Staff"))):
    new_book = models.Book(title=request.title,author=request.author,quantity=request.quantity,instock=request.instock,price=request.price)
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return new_book

@router.post('/create/csv')
def create_book_csv(db: Session = Depends(get_db), current_user: dict = Depends(require_role("Admin","Staff")),file: UploadFile = File(...)):

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")
    
    content = file.file.read().decode("utf-8").splitlines()
    reader = csv.DictReader(content)

    added_books = []
    for row in reader:
        if not row.get("title") or not row.get("author"):
            continue
        try:
            price = int(row.get("price", 0))
            quantity = int(row.get("stock", 0))
            genre_id = int(row.get("genre_id", 1))
        except ValueError:
            continue  

        book = models.Book(
            title=row["title"],
            author=row["author"],
            price=price,
            quantity=quantity,
            genre_id=genre_id,
            instock=True
        )
        db.add(book)
        added_books.append(book.title)

    db.commit()

    return {
        "message": f"Added {len(added_books)} books successfully",
        "books": added_books
    }

@router.post('/create/isbn/{isbn}')
def create_books_isbn(isbn: str, db: Session = Depends(get_db), current_user: dict = Depends(require_role("Admin", "Staff"))):
    CATEGORY_TO_GENRE_ID = {
        "History": 2,
        "Philosophy": 3,
        "Literature": 4,
        "Science": 5,
        "Fiction": 6
    }

    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    response = requests.get(url)
    
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Error contacting Google Books API")
    
    data = response.json()
    if "items" not in data or len(data["items"]) == 0:
        raise HTTPException(status_code=404, detail="Book not found on Google Books")
    
    book_info = data["items"][0]["volumeInfo"]

    title = book_info.get("title", "Unknown Title")
    authors = ", ".join(book_info.get("authors", ["Unknown Author"]))
    categories = book_info.get("categories", [])

    if categories:
        genre_name = categories[0]
        genre_id = CATEGORY_TO_GENRE_ID.get(genre_name, random.choice([4, 5]))
    else:
        genre_id = 1

    price = 0.0
    stock = 10
    is_available = True

    existing_book = db.query(models.Book).filter(models.Book.title==title, models.Book.author==authors).first()
    if existing_book:
        raise HTTPException(status_code=409, detail="Book already exists in the database")

    new_book = models.Book(
        title=title,
        author=authors,
        genre_id=genre_id,
        price=price,
        quantity=stock,
        instock=is_available
    )
    db.add(new_book)
    db.commit()
    db.refresh(new_book)

    return {
        "message": "Book added successfully",
        "book_id": new_book.id,
        "title": title,
        "author": authors,
        "genre_id": genre_id,
        "price": price,
        "stock": stock
    }

@router.get('/get/{id}')
def get_book(id: int, db: Session = Depends(get_db), current_user: dict = Depends(require_role("Admin","Staff"))):
    book_with_id = db.query(models.Book).filter(models.Book.id == id).first()
    if not book_with_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"book with id {id} not found")
    return book_with_id

@router.delete('/delete/{id}')
def delete_book(id: int, db: Session = Depends(get_db), current_user: dict = Depends(require_role("Admin","Staff"))):
    books = db.query(models.Book).filter(models.Book.id == id).first()
    if not books:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"book with id {id} not found")
    db.delete(books)
    db.commit()
    return {"message": f"Book with {id} deleted"}

@router.put('/update/{id}')
def update_book(id: int,request: Book, db: Session = Depends(get_db), current_user: dict = Depends(require_role("Admin","Staff"))):
    book_id = db.query(models.Book).filter(models.Book.id == id).first()
    if not book_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"book with id {id} not found")
    
    book_id.title = request.title
    book_id.author = request.author
    book_id.quantity = request.quantity
    book_id.instock = request.instock
    book_id.genre_id = request.genre_id
    book_id.price = request.price

    db.commit()
    db.refresh(book_id)

    return {"message": "Details of the book updated",
            "current_title": f"{request.title}",
            "current_author": f"{request.author}",
            "current_quantity": "f{request.quantity}",
            "current_availability": f"{request.instock}",
            "current_price": f"{request.price}",
            }

