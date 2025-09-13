from pickle import FALSE

from fastapi import FastAPI, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import sqlite3
import random

# ---------------------------
# 1. Create FastAPI app
# ---------------------------
app = FastAPI()

# ---------------------------
# 2. Database Setup
# ---------------------------
DB_NAME = "water_ai.db"
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()

# Create table if not exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS houses (
    user_id TEXT PRIMARY KEY,
    house_size INTEGER,
    residents INTEGER,
    capacity INTEGER,
    current_storage INTEGER,
    daily_usage INTEGER
)
""")
conn.commit()

# ---------------------------
# 3. Serve Static Files
# ---------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/",include_in_schema=False)
def serve_index():
    """Serve the frontend (index.html)"""
    return FileResponse("static/index.html")

# ---------------------------
# 4. API Endpoints
# ---------------------------

@app.post("/register")
def register(
    user_id: str = Form(...),
    house_size: int = Form(...),
    residents: int = Form(...),
    capacity: int = Form(...)
):
    """Register a house and save it to the database"""
    cursor.execute(
        "INSERT OR REPLACE INTO houses VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, house_size, residents, capacity, capacity, 0)
    )
    conn.commit()
    return {"message": "House registered successfully", "user_id": user_id}


@app.get("/dashboard/{user_id}")
def dashboard(user_id: str):
    """Fetch and update water usage for a specific house"""
    cursor.execute("SELECT * FROM houses WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    if not row:
        return JSONResponse(content={"error": "User not found"}, status_code=404)

    user_id, house_size, residents, capacity, current_storage, daily_usage = row

    # Simulate water usage
    usage_today = random.randint(5, 25)
    new_storage = max(0, current_storage - usage_today)
    new_daily = daily_usage + usage_today

    # Update DB
    cursor.execute(
        "UPDATE houses SET current_storage=?, daily_usage=? WHERE user_id=?",
        (new_storage, new_daily, user_id)
    )
    conn.commit()

    # Daily limit
    daily_limit = residents * 135
    excess = max(0, new_daily - daily_limit)
    fine_amount = excess * 5

    status = "Within Limit" if excess == 0 else "Over Limit"

    return {
        "user_id": user_id,
        "house_size": house_size,
        "residents": residents,
        "capacity": capacity,
        "current_storage": f"{new_storage} L / {capacity} L",
        "daily_usage": f"{new_daily} L / {daily_limit} L",
        "status": status,
        "excess_usage": excess,
        "fine_amount": fine_amount
    }

@app.get("/test")
def test_page():
    return FileResponse("static/index.html")

@app.get("/admin")
def admin_dashboard():
    """Admin: View all houses and usage"""
    cursor.execute("SELECT * FROM houses")
    rows = cursor.fetchall()
    all_data = []
    for row in rows:
        user_id, house_size, residents, capacity, current_storage, daily_usage = row
        daily_limit = residents * 135
        excess = max(0, daily_usage - daily_limit)
        fine_amount = excess * 5
        status = "Within Limit" if excess == 0 else "Over Limit"

        all_data.append({
            "user_id": user_id,
            "house_size": house_size,
            "residents": residents,
            "capacity": capacity,
            "current_storage": f"{current_storage} L / {capacity} L",
            "daily_usage": f"{daily_usage} L / {daily_limit} L",
            "status": status,
            "excess_usage": excess,
            "fine_amount": fine_amount
        })
    return {"houses": all_data}
