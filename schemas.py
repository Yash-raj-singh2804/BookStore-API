from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

class Book(BaseModel):
    title: str
    author: str
    instock: bool
    quantity: int
    genre_id: int
    price: int

class BookResponse(Book):   
    id: int

    class Config:
        from_attributes = True

class BookOut(BaseModel):
    id: int
    title: str

class User(BaseModel):
    name: str
    email: EmailStr
    password: str 
    role: str = "Customer"

class UserResponse(User):   
    id: int

    class Config:
        from_attributes = True

class Genre(BaseModel):
    name: str

class GenreResponse(Genre):   
    id: int

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None

class Order(BaseModel):
    user_id: int
    total_amount: int
    status: str
    created_at: datetime
    updated_at: datetime

class OrderResponse(Order):
    order_id: int

    class Config:
        from_attributes = True

class OrderOut(BaseModel):
    id: int
    user_id: int
    total_amount: int

class OrderItem(BaseModel):
    order_id: int
    book_id: int
    quantity: int
    price: int

class OrderItemResponse(OrderItem):
    orderitem_id: int

    class Config:
        from_attributes = True

class Cart(BaseModel):
    user_id: int
    status: str  
    created_at: datetime

class CartResponse(Cart):
    cart_id: int

    class Config:
        from_attributes = True

class CartItem(BaseModel):
    cart_id: int
    book_id: int
    quantity: int

class CartItemResponse(CartItem):
    cartitem_id: int

    class Config:
        from_attributes = True

class addtocart(BaseModel):
    quantity: int
    book_id: int

class CartitemUpdate(BaseModel):
    book_id: Optional[int] = None
    quantity: Optional[int] = None
    
class OrderItemCreate(BaseModel):
    book_id: int
    quantity: int

class OrderCreate(BaseModel):
    items: List[OrderItemCreate]

class OrderStatusUpdate(BaseModel):
    status: Optional[str] = None

class GenreCreate(BaseModel):
    name: str