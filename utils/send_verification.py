from fastapi_mail import FastMail, MessageSchema
from config import conf
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()
url_link = os.getenv("URL_LINK")

fm = FastMail(conf)

async def send_verification_email(email: str, token: str):
    verify_link = f"url_link/verify/{token}"

    html = f"""
    <h3>Welcome to Fern & Folio 📚</h3>
    <p>Click the link below to verify your email:</p>
    <a href="{verify_link}" target="_blank">Verify Email</a>
    <p>This link will expire in 24 hours.</p>
    """

    message = MessageSchema(
        subject="Verify your email",
        recipients=[email],
        body=html,
        subtype="html"
    )

    await fm.send_message(message)

async def send_email_order(customer_name: str, order_id: int, total_amount: int, customer_email: str, order_list: List):
    html = f"""
    <h3>Thank you for ordering from Fern & Folio 📚</h3>
    <p>Hey {customer_name}, thanks for ordering from Fern & Folio. Your order id {order_id} and total amount is {total_amount}. We’re preparing your books and will notify you once they're shipped.</p>
    <p>Your order: {order_list}<p/>
    <p>Happy Reading,
    Fern & Folio Team</p>
    """

    message = MessageSchema(
        subject="Order from Fern & Folio 📚",
        recipients=[customer_email],
        body=html,
        subtype="html"
    )

    await fm.send_message(message)