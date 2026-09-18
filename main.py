from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from datetime import datetime

app = FastAPI(title="SkillEdge Backend")


# -------------------------
# CORS (Strictly Allowed Origins)
# -------------------------

origins = [
    "https://skilledge-frontend-1.onrender.com",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------
# Database
# -------------------------

DATABASE = "skilledge.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_database():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            service TEXT NOT NULL,
            address TEXT NOT NULL,
            booking_date TEXT NOT NULL,
            message TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


create_database()


# -------------------------
# Booking Model
# -------------------------

class Booking(BaseModel):
    name: str
    phone: str
    service: str
    address: str
    booking_date: str
    message: str = ""


# -------------------------
# Home & Health
# -------------------------

@app.get("/")
def home():
    return {
        "message": "SkillEdge Backend is running",
        "status": "success"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# -------------------------
# Create Booking
# -------------------------

@app.post("/bookings")
def create_booking(booking: Booking):

    conn = get_db()

    created_at = datetime.now().isoformat()

    cursor = conn.execute("""
        INSERT INTO bookings
        (
            name,
            phone,
            service,
            address,
            booking_date,
            message,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        booking.name,
        booking.phone,
        booking.service,
        booking.address,
        booking.booking_date,
        booking.message,
        "Pending",
        created_at
    ))

    booking_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return {
        "success": True,
        "message": "Booking created successfully",
        "booking_id": booking_id,
        "status": "Pending"
    }


# -------------------------
# Get All Bookings
# -------------------------

@app.get("/bookings")
def get_bookings():

    conn = get_db()

    rows = conn.execute("""
        SELECT *
        FROM bookings
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return [dict(row) for row in rows]


# -------------------------
# Get Single Booking
# -------------------------

@app.get("/bookings/{booking_id}")
def get_booking(booking_id: int):

    conn = get_db()

    row = conn.execute("""
        SELECT *
        FROM bookings
        WHERE id = ?
    """, (booking_id,)).fetchone()

    conn.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    return dict(row)


# -------------------------
# Update Booking Status
# -------------------------

@app.patch("/bookings/{booking_id}/status")
def update_booking_status(
    booking_id: int,
    status: str
):

    allowed_statuses = [
        "Pending",
        "Accepted",
        "Rejected",
        "Cancelled",
        "Completed"
    ]

    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid status"
        )

    conn = get_db()

    cursor = conn.execute("""
        UPDATE bookings
        SET status = ?
        WHERE id = ?
    """, (status, booking_id))

    conn.commit()

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    conn.close()

    return {
        "success": True,
        "message": "Booking status updated",
        "booking_id": booking_id,
        "status": status
    }
