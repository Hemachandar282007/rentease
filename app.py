import os
import json
import random
import string
import urllib.parse
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, abort
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from db import get_db_connection, init_db

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "rentease-collegiate-pfs-secret-2026")

UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads", "rooms")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize database schema and seeds on startup
with app.app_context():
    init_db()


# -----------------------------------------------------------------------------
# Context Processors & Security Decorators
# -----------------------------------------------------------------------------

@app.context_processor
def inject_current_user():
    """Injects user authentication state into all rendered templates."""
    user = None
    if "user_id" in session:
        conn = get_db_connection()
        user = conn.execute("SELECT id, name, email, role, college, phone, avatar_initials FROM users WHERE id = ?", (session["user_id"],)).fetchone()
        conn.close()
    return {"current_user": user}


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to access this feature.", "warning")
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Admin access requires authentication.", "warning")
            return redirect(url_for("login", mode="admin", next=request.url))
        if session.get("user_role") != "admin":
            flash("Access denied. Administrator privileges are required.", "error")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return decorated_function


# -----------------------------------------------------------------------------
# Authentication Routes
# -----------------------------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    """Unified login for Students and Administrators with mode toggle."""
    mode = request.args.get("mode", "student")
    next_url = request.args.get("next") or request.form.get("next")

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        login_role = request.form.get("role", "student")

        if not email or not password:
            flash("Please enter both email and password.", "error")
            return render_template("auth/login.html", mode=login_role, next=next_url)

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email,)).fetchone()
        conn.close()

        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password. Please check your credentials.", "error")
            return render_template("auth/login.html", mode=login_role, next=next_url)

        session.clear()
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["user_email"] = user["email"]
        session["user_role"] = user["role"]
        session["user_initials"] = user["avatar_initials"]

        flash(f"Welcome back, {user['name']}!", "success")

        if user["role"] == "admin":
            return redirect(next_url or url_for("admin_dashboard"))
        return redirect(next_url or url_for("student_dashboard"))

    return render_template("auth/login.html", mode=mode, next=next_url)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Student registration route."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        phone = request.form.get("phone", "").strip()
        college = request.form.get("college", "").strip()
        role = request.form.get("role", "student")

        if not name or not email or not password:
            flash("Full name, email, and password are required.", "error")
            return render_template("auth/register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "error")
            return render_template("auth/register.html")

        parts = name.split()
        initials = (parts[0][0] + (parts[1][0] if len(parts) > 1 else "")).upper()

        conn = get_db_connection()
        existing = conn.execute("SELECT id FROM users WHERE LOWER(email) = ?", (email,)).fetchone()
        if existing:
            conn.close()
            flash("An account with this email already exists. Please log in.", "error")
            return redirect(url_for("login"))

        conn.execute("""
            INSERT INTO users (name, email, password_hash, role, phone, college, avatar_initials)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, email, generate_password_hash(password), role, phone, college, initials))
        conn.commit()

        new_user = conn.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email,)).fetchone()
        conn.close()

        session.clear()
        session["user_id"] = new_user["id"]
        session["user_name"] = new_user["name"]
        session["user_email"] = new_user["email"]
        session["user_role"] = new_user["role"]
        session["user_initials"] = new_user["avatar_initials"]

        flash(f"Account registered successfully! Welcome to RentEase, {name}.", "success")
        return redirect(url_for("listings"))

    return render_template("auth/register.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("home"))


# -----------------------------------------------------------------------------
# Home & Public Pages
# -----------------------------------------------------------------------------

@app.route("/")
def home():
    """Landing view for RentEase with dynamic metrics and top listings."""
    conn = get_db_connection()

    total_rooms = conn.execute("SELECT COUNT(*) FROM listings").fetchone()[0]
    total_students = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'student'").fetchone()[0]
    avg_rating_row = conn.execute("SELECT AVG(rating) FROM listings").fetchone()[0]
    avg_rating = round(avg_rating_row, 1) if avg_rating_row else 4.7

    stats = [
        {"value": f"{total_rooms}+", "label": "Verified Rooms Near Campus"},
        {"value": f"{total_students}+", "label": "Active Student Seekers"},
        {"value": f"{avg_rating}/5", "label": "Average Resident Rating"},
    ]

    features = [
        {
            "tag": "01",
            "title": "Search Verified PGs & Rooms",
            "text": "Filter verified student rooms by walking distance from gate, monthly budget, and amenities.",
        },
        {
            "tag": "02",
            "title": "Match Lifestyle-Compatible Roommates",
            "text": "Discover peers sharing your sleep cycles, study habits, and dietary preferences.",
        },
        {
            "tag": "03",
            "title": "Schedule In-Person Room Visits",
            "text": "Book direct visit slots with verified property owners and track confirmation in real-time.",
        },
        {
            "tag": "04",
            "title": "Instant Token Spot Reservation",
            "text": "Reserve room vacancies with a ₹500 advance token deposit and instant digital receipt.",
        },
    ]

    featured_listings = conn.execute("""
        SELECT * FROM listings ORDER BY rating DESC LIMIT 4
    """).fetchall()

    conn.close()
    return render_template("home.html", stats=stats, features=features, listings=featured_listings)


# -----------------------------------------------------------------------------
# Listings & Search
# -----------------------------------------------------------------------------

@app.route("/listings")
def listings():
    """Listings directory with search, filter controls, and image gallery support."""
    q = request.args.get("q", "").strip()
    room_type = request.args.get("room_type", "")
    gender_pref = request.args.get("gender_pref", "")
    max_rent = request.args.get("max_rent", type=int)

    conn = get_db_connection()
    query = "SELECT * FROM listings WHERE 1=1"
    params = []

    if q:
        query += " AND (name LIKE ? OR area LIKE ? OR address LIKE ? OR amenities LIKE ?)"
        term = f"%{q}%"
        params.extend([term, term, term, term])

    if room_type:
        query += " AND room_type = ?"
        params.append(room_type)

    if gender_pref:
        query += " AND (gender_pref = ? OR gender_pref = 'Any')"
        params.append(gender_pref)

    if max_rent:
        query += " AND rent_monthly <= ?"
        params.append(max_rent)

    query += " ORDER BY id DESC"
    all_listings = conn.execute(query, params).fetchall()

    saved_ids = []
    if "user_id" in session:
        rows = conn.execute("SELECT listing_id FROM saved_listings WHERE user_id = ?", (session["user_id"],)).fetchall()
        saved_ids = [r["listing_id"] for r in rows]

    conn.close()

    return render_template(
        "listings/index.html",
        listings=all_listings,
        saved_ids=saved_ids,
        search_query=q,
        room_type=room_type,
        gender_pref=gender_pref,
        max_rent=max_rent,
    )


@app.route("/api/listings")
def api_listings():
    """JSON API returning listings for client-side search & filtering."""
    q = request.args.get("q", "").strip()
    room_type = request.args.get("room_type", "")
    gender_pref = request.args.get("gender_pref", "")
    max_rent = request.args.get("max_rent", type=int)

    conn = get_db_connection()
    query = "SELECT * FROM listings WHERE 1=1"
    params = []

    if q:
        query += " AND (name LIKE ? OR area LIKE ? OR address LIKE ? OR amenities LIKE ?)"
        term = f"%{q}%"
        params.extend([term, term, term, term])

    if room_type:
        query += " AND room_type = ?"
        params.append(room_type)

    if gender_pref:
        query += " AND (gender_pref = ? OR gender_pref = 'Any')"
        params.append(gender_pref)

    if max_rent:
        query += " AND rent_monthly <= ?"
        params.append(max_rent)

    query += " ORDER BY id DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    data = []
    for r in rows:
        images = []
        if r["images"]:
            try:
                images = json.loads(r["images"])
            except Exception:
                images = [r["image_url"]] if r["image_url"] else []
        elif r["image_url"]:
            images = [r["image_url"]]

        data.append({
            "id": r["id"],
            "name": r["name"],
            "area": r["area"],
            "address": r["address"],
            "rent_monthly": r["rent_monthly"],
            "deposit": r["deposit"],
            "room_type": r["room_type"],
            "gender_pref": r["gender_pref"],
            "amenities": r["amenities"].split(", ") if r["amenities"] else [],
            "status": r["status"],
            "status_kind": r["status_kind"],
            "rating": r["rating"],
            "reviews_count": r["reviews_count"],
            "description": r["description"],
            "image_url": r["image_url"],
            "images": images,
            "contact_phone": r["contact_phone"]
        })
    return jsonify(data)


# -----------------------------------------------------------------------------
# Booking, Payments & WhatsApp Notifications
# -----------------------------------------------------------------------------

@app.route("/api/book-visit", methods=["POST"])
@login_required
def book_visit():
    """Schedules an in-person room visit and dispatches automated notifications."""
    data = request.get_json() or request.form
    listing_id = data.get("listing_id")
    visit_date = data.get("visit_date")
    visit_time = data.get("visit_time")
    message = data.get("message", "").strip()

    if not listing_id or not visit_date or not visit_time:
        return jsonify({"success": False, "error": "Missing listing ID, visit date, or preferred time."}), 400

    conn = get_db_connection()
    listing = conn.execute("SELECT name, contact_phone FROM listings WHERE id = ?", (listing_id,)).fetchone()
    user = conn.execute("SELECT name, email, phone FROM users WHERE id = ?", (session["user_id"],)).fetchone()

    conn.execute("""
        INSERT INTO visit_requests (listing_id, user_id, visit_date, visit_time, message, status)
        VALUES (?, ?, ?, ?, ?, 'Pending')
    """, (listing_id, session["user_id"], visit_date, visit_time, message))

    # Log notification alerts
    listing_name = listing["name"] if listing else "Campus PG"
    student_name = user["name"] if user else "Student"

    conn.execute("""
        INSERT INTO notifications (user_id, title, message, channel, recipient_contact, status)
        VALUES (?, ?, ?, 'WhatsApp', ?, 'Delivered')
    """, (
        session["user_id"],
        "Visit Request Dispatched",
        f"Your appointment request for {listing_name} on {visit_date} at {visit_time} was submitted. Host phone: {listing['contact_phone'] if listing else '+91 98421 00100'}",
        user["phone"] or "+91 98421 00000"
    ))

    conn.execute("""
        INSERT INTO notifications (user_id, title, message, channel, recipient_contact, status)
        VALUES (?, ?, ?, 'Email', ?, 'Delivered')
    """, (
        session["user_id"],
        f"Visit Confirmation Pending: {listing_name}",
        f"Dear {student_name}, your visit request has been queued. You will be notified once the owner confirms.",
        user["email"]
    ))

    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Visit scheduled successfully! WhatsApp & Email alerts queued."})


@app.route("/api/token-booking", methods=["POST"])
@login_required
def token_booking():
    """Processes advance token deposit (₹500), creates receipt, and triggers alerts."""
    data = request.get_json() or request.form
    listing_id = data.get("listing_id")
    amount = data.get("amount", 500)
    payment_method = data.get("payment_method", "UPI / Google Pay")
    payment_details = data.get("payment_details", "upi-student@okhdfcbank")

    if not listing_id:
        return jsonify({"success": False, "error": "Listing ID is required."}), 400

    conn = get_db_connection()
    listing = conn.execute("SELECT * FROM listings WHERE id = ?", (listing_id,)).fetchone()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()

    if not listing:
        conn.close()
        return jsonify({"success": False, "error": "Listing not found."}), 404

    # Generate unique payment ID and receipt number
    rand_suffix = "".join(random.choices(string.digits, k=4))
    payment_id = f"PAY-RE-2026-{rand_suffix}"
    receipt_num = f"REC-2026-{rand_suffix}"

    conn.execute("""
        INSERT INTO payments (payment_id, user_id, listing_id, amount, payment_method, payment_details, status, receipt_number)
        VALUES (?, ?, ?, ?, ?, ?, 'Success', ?)
    """, (payment_id, session["user_id"], listing_id, amount, payment_method, payment_details, receipt_num))

    # Mark listing as "1 spot left" or reserve spot
    if listing["status"] == "Vacant":
        conn.execute("UPDATE listings SET status = '1 spot left', status_kind = 'low' WHERE id = ?", (listing_id,))

    # Log WhatsApp & Email confirmation
    now_str = datetime.now().strftime("%d %b %Y, %I:%M %p")
    conn.execute("""
        INSERT INTO notifications (user_id, title, message, channel, recipient_contact, status)
        VALUES (?, ?, ?, 'WhatsApp', ?, 'Delivered')
    """, (
        session["user_id"],
        "Advance Spot Reserved",
        f"Payment of ₹{amount} received for {listing['name']}. Receipt #{receipt_num} generated. Spot held for 7 days.",
        user["phone"] or "+91 98421 00000"
    ))

    conn.execute("""
        INSERT INTO notifications (user_id, title, message, channel, recipient_contact, status)
        VALUES (?, ?, ?, 'Email', ?, 'Delivered')
    """, (
        session["user_id"],
        f"Token Booking Receipt: {receipt_num}",
        f"Thank you {user['name']}. Your advance token of ₹{amount} for {listing['name']} is confirmed.",
        user["email"]
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "payment_id": payment_id,
        "receipt_number": receipt_num,
        "listing_name": listing["name"],
        "amount": amount,
        "date": now_str,
        "student_name": user["name"],
        "payment_method": payment_method
    })


@app.route("/api/receipt/<payment_id>")
@login_required
def get_receipt(payment_id):
    """Fetches details of a verified receipt."""
    conn = get_db_connection()
    receipt = conn.execute("""
        SELECT p.*, l.name as listing_name, l.area, l.rent_monthly, u.name as student_name, u.email as student_email, u.phone as student_phone
        FROM payments p
        JOIN listings l ON p.listing_id = l.id
        JOIN users u ON p.user_id = u.id
        WHERE p.payment_id = ?
    """, (payment_id,)).fetchone()
    conn.close()

    if not receipt:
        return jsonify({"success": False, "error": "Receipt not found."}), 404

    return jsonify({
        "success": True,
        "receipt": {
            "payment_id": receipt["payment_id"],
            "receipt_number": receipt["receipt_number"],
            "amount": receipt["amount"],
            "payment_method": receipt["payment_method"],
            "status": receipt["status"],
            "created_at": receipt["created_at"],
            "listing_name": receipt["listing_name"],
            "area": receipt["area"],
            "rent_monthly": receipt["rent_monthly"],
            "student_name": receipt["student_name"],
            "student_email": receipt["student_email"],
            "student_phone": receipt["student_phone"]
        }
    })


@app.route("/api/whatsapp-link/<int:listing_id>")
def whatsapp_link(listing_id):
    """Generates direct pre-filled WhatsApp click-to-chat URL."""
    conn = get_db_connection()
    listing = conn.execute("SELECT name, area, rent_monthly, contact_phone FROM listings WHERE id = ?", (listing_id,)).fetchone()
    conn.close()

    if not listing:
        return jsonify({"success": False, "error": "Listing not found"}), 404

    phone = listing["contact_phone"] or "+919842100100"
    cleaned_phone = "".join(filter(str.isdigit, phone))

    user_name = session.get("user_name", "a student")
    msg = f"Hello! I am {user_name} from KSRCT. I am interested in inquiring about '{listing['name']}' ({listing['area']}) listed on RentEase for ₹{listing['rent_monthly']:,}/mo. Is a visit slot available?"

    wa_url = f"https://wa.me/{cleaned_phone}?text={urllib.parse.quote(msg)}"
    return jsonify({"success": True, "url": wa_url})


@app.route("/api/save-listing", methods=["POST"])
@login_required
def toggle_save_listing():
    """Toggles bookmarking a listing for the student."""
    data = request.get_json() or request.form
    listing_id = data.get("listing_id")
    if not listing_id:
        return jsonify({"success": False, "error": "Listing ID required"}), 400

    conn = get_db_connection()
    existing = conn.execute("SELECT * FROM saved_listings WHERE user_id = ? AND listing_id = ?", (session["user_id"], listing_id)).fetchone()

    if existing:
        conn.execute("DELETE FROM saved_listings WHERE user_id = ? AND listing_id = ?", (session["user_id"], listing_id))
        saved = False
    else:
        conn.execute("INSERT INTO saved_listings (user_id, listing_id) VALUES (?, ?)", (session["user_id"], listing_id))
        saved = True

    conn.commit()
    conn.close()
    return jsonify({"success": True, "saved": saved})


# -----------------------------------------------------------------------------
# Roommate Matching System
# -----------------------------------------------------------------------------

@app.route("/roommates")
def roommates():
    """Roommate matching discovery page."""
    conn = get_db_connection()
    profiles = conn.execute("""
        SELECT rp.*, u.name, u.email, u.phone, u.college, u.avatar_initials
        FROM roommate_profiles rp
        JOIN users u ON rp.user_id = u.id
        ORDER BY rp.id DESC
    """).fetchall()

    my_profile = None
    if "user_id" in session:
        my_profile = conn.execute("SELECT * FROM roommate_profiles WHERE user_id = ?", (session["user_id"],)).fetchone()

    conn.close()
    return render_template("roommates/index.html", profiles=profiles, my_profile=my_profile)


@app.route("/roommates/profile", methods=["POST"])
@login_required
def save_roommate_profile():
    """Creates or updates current user's roommate lifestyle profile."""
    bio = request.form.get("bio", "").strip()
    budget_max = request.form.get("budget_max", 7000, type=int)
    sleep_schedule = request.form.get("sleep_schedule", "Flexible")
    cleanliness = request.form.get("cleanliness", "Moderate")
    study_habit = request.form.get("study_habit", "Silent Study")
    food_pref = request.form.get("food_pref", "Any")
    major = request.form.get("major", "").strip()
    graduation_year = request.form.get("graduation_year", "").strip()
    gender = request.form.get("gender", "Any").strip()

    conn = get_db_connection()
    existing = conn.execute("SELECT id FROM roommate_profiles WHERE user_id = ?", (session["user_id"],)).fetchone()

    if existing:
        conn.execute("""
            UPDATE roommate_profiles
            SET bio=?, budget_max=?, sleep_schedule=?, cleanliness=?, study_habit=?,
                food_pref=?, major=?, graduation_year=?, gender=?
            WHERE user_id=?
        """, (bio, budget_max, sleep_schedule, cleanliness, study_habit, food_pref, major, graduation_year, gender, session["user_id"]))
        flash("Your roommate preference profile has been updated!", "success")
    else:
        conn.execute("""
            INSERT INTO roommate_profiles (user_id, bio, budget_max, sleep_schedule, cleanliness, study_habit, food_pref, major, graduation_year, gender)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (session["user_id"], bio, budget_max, sleep_schedule, cleanliness, study_habit, food_pref, major, graduation_year, gender))
        flash("Your roommate profile is live in the register!", "success")

    conn.commit()
    conn.close()
    return redirect(url_for("roommates"))


# -----------------------------------------------------------------------------
# Student Dashboard
# -----------------------------------------------------------------------------

@app.route("/dashboard")
@login_required
def student_dashboard():
    """Personal dashboard showing visits, saved rooms, payments, and notifications."""
    conn = get_db_connection()
    user_id = session["user_id"]

    visits = conn.execute("""
        SELECT vr.*, l.name as listing_name, l.area, l.rent_monthly, l.contact_phone
        FROM visit_requests vr
        JOIN listings l ON vr.listing_id = l.id
        WHERE vr.user_id = ?
        ORDER BY vr.id DESC
    """, (user_id,)).fetchall()

    saved = conn.execute("""
        SELECT l.*
        FROM saved_listings sl
        JOIN listings l ON sl.listing_id = l.id
        WHERE sl.user_id = ?
        ORDER BY sl.created_at DESC
    """, (user_id,)).fetchall()

    payments = conn.execute("""
        SELECT p.*, l.name as listing_name, l.area, l.rent_monthly
        FROM payments p
        JOIN listings l ON p.listing_id = l.id
        WHERE p.user_id = ?
        ORDER BY p.id DESC
    """, (user_id,)).fetchall()

    notifications = conn.execute("""
        SELECT * FROM notifications
        WHERE user_id = ?
        ORDER BY id DESC LIMIT 10
    """, (user_id,)).fetchall()

    roommate_profile = conn.execute("SELECT * FROM roommate_profiles WHERE user_id = ?", (user_id,)).fetchone()

    conn.close()
    return render_template(
        "dashboard/student.html",
        visits=visits,
        saved_listings=saved,
        payments=payments,
        notifications=notifications,
        roommate_profile=roommate_profile
    )


# -----------------------------------------------------------------------------
# Admin Management Portal
# -----------------------------------------------------------------------------

@app.route("/admin")
@admin_required
def admin_dashboard():
    """Administrator operations desk with KPIs, payments, visits, and listings."""
    conn = get_db_connection()

    total_listings = conn.execute("SELECT COUNT(*) FROM listings").fetchone()[0]
    vacant_listings = conn.execute("SELECT COUNT(*) FROM listings WHERE status = 'Vacant'").fetchone()[0]
    total_students = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'student'").fetchone()[0]
    pending_visits = conn.execute("SELECT COUNT(*) FROM visit_requests WHERE status = 'Pending'").fetchone()[0]

    revenue_row = conn.execute("SELECT SUM(amount) FROM payments").fetchone()[0]
    total_revenue = revenue_row if revenue_row else 0

    all_listings = conn.execute("SELECT * FROM listings ORDER BY id DESC").fetchall()
    all_visits = conn.execute("""
        SELECT vr.*, l.name as listing_name, u.name as student_name, u.email as student_email, u.phone as student_phone
        FROM visit_requests vr
        JOIN listings l ON vr.listing_id = l.id
        JOIN users u ON vr.user_id = u.id
        ORDER BY vr.id DESC
    """).fetchall()

    all_payments = conn.execute("""
        SELECT p.*, l.name as listing_name, u.name as student_name, u.email as student_email, u.phone as student_phone
        FROM payments p
        JOIN listings l ON p.listing_id = l.id
        JOIN users u ON p.user_id = u.id
        ORDER BY p.id DESC
    """).fetchall()

    all_users = conn.execute("SELECT id, name, email, role, phone, college, created_at FROM users ORDER BY id DESC").fetchall()

    conn.close()
    return render_template(
        "admin/index.html",
        total_listings=total_listings,
        vacant_listings=vacant_listings,
        total_students=total_students,
        pending_visits=pending_visits,
        total_revenue=total_revenue,
        listings=all_listings,
        visits=all_visits,
        payments=all_payments,
        users=all_users
    )


@app.route("/admin/listing/add", methods=["POST"])
@admin_required
def admin_add_listing():
    """Adds a new room or PG listing with image upload or curated presets."""
    name = request.form.get("name", "").strip()
    area = request.form.get("area", "").strip()
    address = request.form.get("address", "").strip()
    rent_monthly = request.form.get("rent_monthly", 6000, type=int)
    deposit = request.form.get("deposit", 10000, type=int)
    room_type = request.form.get("room_type", "Double")
    gender_pref = request.form.get("gender_pref", "Any")
    amenities = request.form.get("amenities", "High-Speed Wi-Fi, 3 Times Food, RO Water").strip()
    status = request.form.get("status", "Vacant")
    contact_phone = request.form.get("contact_phone", "+91 98421 00100").strip()
    description = request.form.get("description", "").strip()
    preset_style = request.form.get("preset_style", "modern")

    # Handle image upload or presets
    image_url = ""
    images_list = []

    if "room_photo" in request.files:
        file = request.files["room_photo"]
        if file and file.filename != "" and allowed_file(file.filename):
            ext = file.filename.rsplit(".", 1)[1].lower()
            unique_name = f"room_{int(datetime.now().timestamp())}_{random.randint(100,999)}.{ext}"
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
            file.save(filepath)
            image_url = f"/static/uploads/rooms/{unique_name}"
            images_list.append(image_url)

    if not image_url:
        presets = {
            "modern": [
                "/static/images/rooms/sunrise_pg.jpg"
            ],
            "cozy": [
                "/static/images/rooms/maple_residency.jpg"
            ],
            "single": [
                "/static/images/rooms/nest_girls_pg.jpg"
            ],
            "luxury": [
                "/static/images/rooms/greenfield_suites.jpg"
            ]
        }
        selected = presets.get(preset_style, presets["modern"])
        image_url = selected[0]
        images_list = selected

    status_kind = "open" if status == "Vacant" else ("low" if status == "1 spot left" else "full")

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO listings (
            name, area, address, rent_monthly, deposit, room_type, gender_pref,
            amenities, status, status_kind, rating, reviews_count, description,
            image_url, images, contact_phone, owner_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 4.8, 1, ?, ?, ?, ?, ?)
    """, (name, area, address, rent_monthly, deposit, room_type, gender_pref,
          amenities, status, status_kind, description, image_url, json.dumps(images_list), contact_phone, session["user_id"]))
    conn.commit()
    conn.close()

    flash(f"Listing '{name}' added with photo gallery!", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/listing/status/<int:listing_id>", methods=["POST"])
@admin_required
def admin_update_listing_status(listing_id):
    new_status = request.form.get("status", "Vacant")
    status_kind = "open" if new_status == "Vacant" else ("low" if new_status == "1 spot left" else "full")

    conn = get_db_connection()
    conn.execute("UPDATE listings SET status = ?, status_kind = ? WHERE id = ?", (new_status, status_kind, listing_id))
    conn.commit()
    conn.close()

    flash("Listing status updated successfully.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/listing/delete/<int:listing_id>", methods=["POST"])
@admin_required
def admin_delete_listing(listing_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM listings WHERE id = ?", (listing_id,))
    conn.commit()
    conn.close()

    flash("Listing removed from registry.", "info")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/visit/<int:visit_id>/<action>", methods=["POST"])
@admin_required
def admin_moderate_visit(visit_id, action):
    new_status = "Confirmed" if action == "confirm" else "Declined"
    conn = get_db_connection()
    conn.execute("UPDATE visit_requests SET status = ? WHERE id = ?", (new_status, visit_id))

    visit = conn.execute("""
        SELECT vr.*, l.name as listing_name, u.phone as student_phone, u.name as student_name
        FROM visit_requests vr
        JOIN listings l ON vr.listing_id = l.id
        JOIN users u ON vr.user_id = u.id
        WHERE vr.id = ?
    """, (visit_id,)).fetchone()

    if visit:
        conn.execute("""
            INSERT INTO notifications (user_id, title, message, channel, recipient_contact, status)
            VALUES (?, ?, ?, 'WhatsApp', ?, 'Delivered')
        """, (
            visit["user_id"],
            f"Visit Status: {new_status}",
            f"Hello {visit['student_name']}, your visit request for {visit['listing_name']} on {visit['visit_date']} ({visit['visit_time']}) was {new_status.lower()}.",
            visit["student_phone"] or "+91 98421 00000"
        ))

    conn.commit()
    conn.close()

    flash(f"Visit request #{visit_id} marked as {new_status} and notification dispatched.", "success")
    return redirect(url_for("admin_dashboard"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
