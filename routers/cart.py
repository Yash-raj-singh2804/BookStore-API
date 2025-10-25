from fastapi import APIRouter, HTTPException, status, Depends
from schemas import addtocart, CartitemUpdate
import models
from datetime import datetime
from routers.rbac import get_current_user, require_role
from fastapi.security import OAuth2PasswordRequestForm
from routers.authtoken import create_access_token
from hashing import hash_password, verify_password
from database import get_db
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/cart",   
    tags=["Carts"]
    )

@router.post('/add')
def add_to_cart(request: addtocart, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    book = db.query(models.Book).filter(models.Book.id == request.book_id).first()
    if not book or book.quantity < request.quantity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not available")
    
    cart = db.query(models.Cart).filter(models.Cart.id == current_user["user_id"]).first()
    if not cart:
        cart = models.Cart(user_id=current_user["user_id"], status="Active", created_at=datetime.utcnow(), updated_at=datetime.utcnow())
        db.add(cart)
        db.commit()
        db.refresh(cart)

    cart_item = db.query(models.CartItem).filter(models.CartItem.cart_id == cart.id, models.CartItem.book_id == book.id).first()
    if cart_item:
        cart_item.quantity += request.quantity
        cart_item.price += cart_item.quantity * book.price
    else:
        cart_item = models.CartItem(cart_id=cart.id, book_id=book.id, quantity=request.quantity, price=book.price * request.quantity)
        db.add(cart_item)

    db.commit()
    db.refresh(cart_item)

    return {
        "cart_id": cart.id,
        "cartitem_id": cart_item.id,
        "book_id": book.id,
        "title": book.title,
        "quantity": cart_item.quantity,
        "price": cart_item.price
    }
        
@router.get('/get/{id}')
def get_cart(id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    cart = db.query(models.Cart).filter(models.Cart.id == id).first()
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cart with id {id} not found")
    return cart

@router.patch('/update/{item_id}')
def update_cart(item_id: int, request: CartitemUpdate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    cart_item = db.query(models.CartItem).filter(models.CartItem.id == item_id).first()
    if not cart_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"item with id {item_id} not found")
    
    update_data = request.dict(exclude_unset=True)

    for key, value in update_data.items():  
        setattr(cart_item, key, value)

    db.commit()        
    db.refresh(cart_item)

    return cart_item

@router.delete('/delete/{item_id}')
def delete_cartitem(item_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    cart_item = db.query(models.CartItem).filter(models.CartItem.id == item_id).first()
    if not cart_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"item with id {item_id} not found") 
    db.delete(cart_item)
    db.commit()
    return {"message": f"item with id {item_id} deleted"}   

@router.delete('/delete/{item_id}')
def clear_cart(item_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = db.query(models.CartItem).filter(models.CartItem.id == item_id).all()
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"cart with id {item_id} not found") 
    
    for item in cart:
        db.delete(item)

    db.commit()
    return {"message": f"cart with id {item_id} cleared"}   