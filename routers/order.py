from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from schemas import OrderCreate, OrderOut, OrderStatusUpdate
import models
from utils.send_verification import send_email_order
from typing import List
from datetime import datetime
from routers.rbac import get_current_user, require_role
from fastapi_mail import MessageSchema
from fastapi.security import OAuth2PasswordRequestForm
from routers.authtoken import create_access_token
from hashing import hash_password, verify_password
from database import get_db
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/order",   
    tags=["Order"]
    )

@router.post("/create")
def create_order(request: OrderCreate, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user["user_id"]
    amount = 0

    for item in request.items:
        book = db.query(models.Book).filter(models.Book.id == item.book_id).first()
        if not book:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Book with id {item.book_id} not available")
        if book.quantity < item.quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Not enough stock for book id {item.book_id}")
        amount += item.quantity * book.price

    new_order = models.Order(user_id=user_id, status="Pending", total_amount=amount, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    order_list = []

    for item in request.items:
        order_item = models.OrderItem(order_id=new_order.id, book_id=item.book_id, quantity=item.quantity, price=book.price)
        book = db.query(models.Book).filter(models.Book.id == item.book_id).first()
        book.quantity -= item.quantity
        order_list.append(item)
        db.add(order_item)
        db.add(book)

    users_id = db.query(models.User).filter(models.User.id == user_id).first()
    customer_email = users_id.email
    customer_name = users_id.name
    order_id = new_order.id
    background_tasks.add_task(send_email_order, customer_name, order_id, amount, customer_email, order_list)

    db.commit()
    db.refresh(new_order)

    return {"order_id": new_order.id, "total_amount": new_order.total_amount, "status": new_order.status}

@router.get('/get/{id}')
def get_order(id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order with id {id} not found")
    
    items = []
    for item in order.items:
        items.append({
            "book_id": item.book_id,
            "quantity": item.quantity,
            "price": item.price
        })

    return {
        "order_id": order.id,
        "user_id": order.user_id,
        "status": order.status,
        "total_amount": order.total_amount,
        "items": items
    }

@router.get('/getmyorders')
def get_my_orders(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    orders = db.query(models.Order).filter(models.Order.user_id == current_user["user_id"]).all()
    if not orders:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No orders of user with id {id}")
    return orders

@router.get('/getallorders', response_model=List[OrderOut])
def get_all_orders(db: Session = Depends(get_db), current_user: dict = Depends(require_role("Admin","Staff"))):
    orders = db.query(models.Order).all()
    if not orders:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No orders")
    return orders

@router.patch('/updatestatus')
def update_status(id: int,  request: OrderStatusUpdate, db: Session = Depends(get_db), current_user: dict = Depends(require_role("Admin","Staff"))):
    order = db.query(models.Order).filter(models.Order.id == id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No order with id {id}")
    
    new_status = request.status
    order.status = new_status
    db.commit()
    db.refresh(order)

    return {"message": f"Order status updated to {new_status}"}

@router.delete('/delete')
def delete_order(id: int, db: Session = Depends(get_db), current_user: dict = Depends(require_role("Admin","Staff"))):
    order = db.query(models.Order).filter(models.Order.id == id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No order with id {id}")
    order.delete()
    db.commit()
    
    return {"message": f"order with id {id} deleted"}
    