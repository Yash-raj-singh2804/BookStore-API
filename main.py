from fastapi import FastAPI, HTTPException, status, Depends
from routers import book, user, cart, order, genre
from middleware import RateLimiterMiddleware
from database import engine
import models

app = FastAPI(title="Fern & Folio",
                  description="""
    Welcome to the Fern & Folio!. A Book store API built using FastAPI, MySQL, etc.

    Features:  
    - Browse books with search, filter, sort, and pagination  
    - Add books via ISBN or CSV upload (admin only)  
    - Manage users, carts and orders 
    - Role Based Access Control (RBAC)
    - Rate limiting using custom middleware (maximum 10 requests per minute)
    - Email registration for verification
    - Password hashed using argon2 algorithm
    - Containerized using Docker and Docker-Compose
    """)

models.Base.metadata.create_all(bind=engine)

app.add_middleware(RateLimiterMiddleware, max_requests=10, window_seconds=60)
app.include_router(book.router)
app.include_router(user.router)
app.include_router(cart.router)
app.include_router(order.router)
app.include_router(genre.router)

