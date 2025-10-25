from database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime
from datetime import datetime
from sqlalchemy.orm import relationship

class Book(Base):
    __tablename__ = "book"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    genre_id = Column(Integer, ForeignKey('genre.id'))
    author = Column(String(255), nullable=False)
    price = Column(Integer, nullable=False)
    instock = Column(Boolean, nullable=False)
    quantity = Column(Integer, nullable=False)

    genre = relationship('Genre', back_populates='books')
    order_items = relationship('OrderItem', back_populates='book')
    cart_items = relationship('CartItem', back_populates='book')

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)  
    is_verified = Column(Boolean, default=False, nullable=False)
    role = Column(String(255), nullable=False)

    orders = relationship('Order', back_populates='user')
    carts = relationship('Cart', back_populates='user')
    tokens = relationship("EmailVerificationToken", back_populates="user")

class Genre(Base):
    __tablename__ = "genre"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)

    books = relationship('Book', back_populates='genre')


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    total_amount = Column(Integer, nullable=False)
    status = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship('User', back_populates='orders')
    items = relationship('OrderItem', back_populates='order', cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_item"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    book_id = Column(Integer, ForeignKey('book.id'))
    quantity = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)

    order = relationship('Order', back_populates='items')
    book = relationship('Book', back_populates='order_items')

class Cart(Base):
    __tablename__ = "cart"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    status = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship('User', back_populates='carts')
    items = relationship('CartItem', back_populates='cart')


class CartItem(Base):
    __tablename__ = "cart_item"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cart_id = Column(Integer, ForeignKey('cart.id'))
    book_id = Column(Integer, ForeignKey('book.id'))
    quantity = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)

    cart = relationship('Cart', back_populates='items')
    book = relationship('Book', back_populates='cart_items')

class EmailVerificationToken(Base):
    __tablename__ = "Email_Verification_Tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    token_hash = Column(String(255), unique=True)
    expires_at = Column(DateTime)
    used = Column(Boolean, default=False)

    user = relationship("User", back_populates="tokens")

class PendingRegistration(Base):
    __tablename__ = "Pending_Registration"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)  # store hashed password
    role = Column(String(255), nullable=False)
    token_hash = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
