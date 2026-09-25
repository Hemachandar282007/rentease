"""
RentEase Database Management Module
Handles schema creation, migrations, seed data, payments, and notifications.
"""

import sqlite3
import os
import json
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rentease.db")


def get_db_connection():
    """Returns a connection with Row factory enabled for dictionary-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Initializes the database schema, handles migrations, and seeds initial data."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'student', -- 'student' or 'admin'
        phone TEXT,
        college TEXT,
        avatar_initials TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Listings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS listings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        area TEXT NOT NULL,
        address TEXT NOT NULL,
        rent_monthly INTEGER NOT NULL,
        deposit INTEGER NOT NULL DEFAULT 0,
        room_type TEXT NOT NULL, -- 'Single', 'Double', 'Triple'
        gender_pref TEXT NOT NULL, -- 'Boys', 'Girls', 'Any'
        amenities TEXT NOT NULL, -- comma separated: 'WiFi, Food, AC, Power Backup'
        status TEXT NOT NULL DEFAULT 'Vacant', -- 'Vacant', '1 spot left', 'Occupied'
        status_kind TEXT NOT NULL DEFAULT 'open', -- 'open', 'low', 'full'
        rating REAL NOT NULL DEFAULT 4.5,
        reviews_count INTEGER NOT NULL DEFAULT 12,
        description TEXT,
        image_url TEXT,
        images TEXT, -- JSON array of image URLs
        contact_phone TEXT,
        owner_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (owner_id) REFERENCES users (id) ON DELETE SET NULL
    );
    """)

    # Check if images column exists (migration for existing db)
    cursor.execute("PRAGMA table_info(listings)")
    cols = [col[1] for col in cursor.fetchall()]
    if "images" not in cols:
        cursor.execute("ALTER TABLE listings ADD COLUMN images TEXT;")

    # 3. Visit Requests Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS visit_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        listing_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        visit_date TEXT NOT NULL,
        visit_time TEXT NOT NULL,
        message TEXT,
        status TEXT NOT NULL DEFAULT 'Pending', -- 'Pending', 'Confirmed', 'Declined'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (listing_id) REFERENCES listings (id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    # 4. Roommate Profiles Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS roommate_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        bio TEXT,
        budget_max INTEGER NOT NULL,
        sleep_schedule TEXT NOT NULL,
        cleanliness TEXT NOT NULL,
        study_habit TEXT NOT NULL,
        food_pref TEXT NOT NULL,
        major TEXT NOT NULL,
        graduation_year TEXT,
        gender TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    # 5. Saved Listings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS saved_listings (
        user_id INTEGER NOT NULL,
        listing_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, listing_id),
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (listing_id) REFERENCES listings (id) ON DELETE CASCADE
    );
    """)

    # 6. Payments / Token Bookings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        payment_id TEXT UNIQUE NOT NULL,
        user_id INTEGER NOT NULL,
        listing_id INTEGER NOT NULL,
        amount INTEGER NOT NULL,
        payment_method TEXT NOT NULL, -- 'UPI / Google Pay', 'Credit/Debit Card', 'Net Banking'
        payment_details TEXT,        -- UPI ID or Masked Card
        status TEXT NOT NULL DEFAULT 'Success',
        receipt_number TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (listing_id) REFERENCES listings (id) ON DELETE CASCADE
    );
    """)

    # 7. Notifications Log Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        channel TEXT NOT NULL, -- 'WhatsApp', 'Email', 'System'
        recipient_contact TEXT,
        status TEXT NOT NULL DEFAULT 'Delivered',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );
    """)

    conn.commit()

    # Seed Initial Data if empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        seed_data(cursor, conn)
    else:
        # If database already seeded, ensure sample photos and payments exist
        seed_images_and_payments(cursor, conn)

    conn.close()


def seed_data(cursor, conn):
    """Seeds realistic initial sample data."""
    admin_pw = generate_password_hash("admin123")
    student_pw = generate_password_hash("student123")

    cursor.execute("""
    INSERT INTO users (name, email, password_hash, role, phone, college, avatar_initials)
    VALUES 
    ('RentEase Administrator', 'admin@rentease.com', ?, 'admin', '+91 98421 00100', 'RentEase Central Administration', 'AD'),
    ('Aarav Sharma', 'student@ksrct.ac.in', ?, 'student', '+91 98421 11223', 'KSR College of Technology (CSE - 3rd Year)', 'AS'),
    ('Priya Sundaram', 'priya@ksrct.ac.in', ?, 'student', '+91 98421 33445', 'KSR College of Technology (ECE - 2nd Year)', 'PS'),
    ('Karthik Raja', 'karthik@ksrct.ac.in', ?, 'student', '+91 98421 55667', 'KSR College of Technology (IT - 4th Year)', 'KR')
    """, (admin_pw, student_pw, student_pw, student_pw))

    admin_id = 1
    student_id = 2

    # High quality photo galleries for listings
    listings = [
        (
            "Sunrise Executive PG",
            "Near KSRCT Gate 2",
            "Plot 14, Gandhi Nagar 2nd Street, Tiruchengode",
            6500,
            10000,
            "Double",
            "Boys",
            "High-Speed Wi-Fi, 3 Times Food, RO Drinking Water, Daily Housekeeping, Power Backup",
            "Vacant",
            "open",
            4.8,
            24,
            "Spacious premium double-sharing rooms just 4 minutes walking distance from Gate 2. Hygienic South Indian home-style meals, 24/7 CCTV surveillance, and dedicated study desks.",
            "/static/images/rooms/sunrise_pg.jpg",
            json.dumps([
                "/static/images/rooms/sunrise_pg.jpg"
            ]),
            "+919842100100",
            admin_id
        ),
        (
            "Maple Garden Residency",
            "0.8 km from campus",
            "12/4 Sengunthar Nagar, Near Reliance Smart Point",
            5200,
            8000,
            "Triple",
            "Boys",
            "High-Speed Wi-Fi, Food Included, Hot Water, Bicycle Parking, Attached Bathroom",
            "1 spot left",
            "low",
            4.6,
            18,
            "Peaceful, green atmosphere ideal for exam preparation. Homely mess food with vegetarian options, solar hot water geyser, and spacious balconies.",
            "/static/images/rooms/maple_residency.jpg",
            json.dumps([
                "/static/images/rooms/maple_residency.jpg"
            ]),
            "+919842100100",
            admin_id
        ),
        (
            "The Nest Women's PG",
            "1.2 km from campus",
            "88 Kumaran Street, Opp. Apollo Pharmacy",
            7000,
            12000,
            "Single",
            "Girls",
            "Air Conditioned, High-Speed Wi-Fi, 3 Meals & Snacks, Full CCTV, Biometric Entry",
            "Vacant",
            "open",
            4.9,
            31,
            "Exclusive, secure gated residence for female students. Strict security, biometric gate entry, air-conditioned single private rooms, and healthy diet meal plans.",
            "/static/images/rooms/nest_girls_pg.jpg",
            json.dumps([
                "/static/images/rooms/nest_girls_pg.jpg"
            ]),
            "+919842100100",
            admin_id
        ),
        (
            "Anna Student Residency",
            "1.5 km from campus",
            "45 Bye-Pass Road, Near New Bus Stand",
            4800,
            6000,
            "Double",
            "Boys",
            "High-Speed Wi-Fi, Self-Cooking Kitchen, Washing Machine, Bike Parking",
            "1 spot left",
            "low",
            4.4,
            15,
            "Affordable sharing accommodation with access to an open shared induction kitchen, automatic washing machine, and spacious parking.",
            "/static/images/rooms/anna_residency.jpg",
            json.dumps([
                "/static/images/rooms/anna_residency.jpg"
            ]),
            "+919842100100",
            admin_id
        ),
        (
            "Greenfield Heritage Suites",
            "0.5 km from campus",
            "Gate 1 Approach Road, Behind Cafe Coffee Day",
            8500,
            15000,
            "Single",
            "Any",
            "Air Conditioned, High-Speed Wi-Fi, Daily Housekeeping, Laundry Service, Gym Access",
            "Vacant",
            "open",
            4.9,
            42,
            "Luxury private student apartments featuring dedicated workstations, high-speed fiber internet, ergonomic study chairs, and access to an indoor gym.",
            "/static/images/rooms/greenfield_suites.jpg",
            json.dumps([
                "/static/images/rooms/greenfield_suites.jpg"
            ]),
            "+919842100100",
            admin_id
        ),
        (
            "Emerald Shared Living",
            "1.8 km from campus",
            "102 Velur Road, Opp. Municipal High School",
            4200,
            5000,
            "Triple",
            "Boys",
            "High-Speed Wi-Fi, RO Water, Dining Hall, 24/7 Security",
            "Vacant",
            "open",
            4.2,
            9,
            "Budget-friendly stay with clean dormitory-style triple sharing rooms, large common recreation hall with TV, and purified RO water.",
            "/static/images/rooms/emerald_living.jpg",
            json.dumps([
                "/static/images/rooms/emerald_living.jpg"
            ]),
            "+919842100100",
            admin_id
        )
    ]

    cursor.executemany("""
    INSERT INTO listings (
        name, area, address, rent_monthly, deposit, room_type, gender_pref, 
        amenities, status, status_kind, rating, reviews_count, description, 
        image_url, images, contact_phone, owner_id
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, listings)

    # Seed Roommate Profiles
    roommates = [
        (
            2,
            "3rd year CSE student building full-stack projects. Usually code till late night, prefer quiet study environment and clean room.",
            6500,
            "Night Owl (2 AM)",
            "Very Neat & Tidy",
            "Silent Study",
            "Vegetarian",
            "B.Tech Computer Science",
            "2026",
            "Male"
        ),
        (
            3,
            "ECE student preparing for competitive exams. Early riser who loves calm mornings, yoga, and listening to low acoustic music while reading.",
            7000,
            "Early Bird (10 PM)",
            "Very Neat & Tidy",
            "Background Music",
            "Vegetarian",
            "B.E Electronics & Communication",
            "2027",
            "Female"
        ),
        (
            4,
            "Final year IT student into competitive gaming and hackathons. Easy-going, flexible with meal timings, loves weekend road trips.",
            5500,
            "Flexible",
            "Moderate",
            "Group Study",
            "Non-Vegetarian",
            "B.Tech Information Technology",
            "2025",
            "Male"
        )
    ]

    cursor.executemany("""
    INSERT INTO roommate_profiles (
        user_id, bio, budget_max, sleep_schedule, cleanliness, 
        study_habit, food_pref, major, graduation_year, gender
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, roommates)

    cursor.execute("""
    INSERT INTO visit_requests (listing_id, user_id, visit_date, visit_time, message, status)
    VALUES 
    (1, 2, '2026-09-20', '04:30 PM', 'Would like to inspect the double room and verify internet bandwidth.', 'Confirmed'),
    (2, 2, '2026-09-22', '11:00 AM', 'Interested in checking the attached bathroom and meal options.', 'Pending'),
    (3, 3, '2026-09-21', '05:00 PM', 'Visiting with parent to inspect security and single room availability.', 'Confirmed')
    """)

    cursor.execute("""
    INSERT INTO saved_listings (user_id, listing_id)
    VALUES (2, 1), (2, 3)
    """)

    # Seed initial payment & notifications for demo student Aarav
    cursor.execute("""
    INSERT INTO payments (payment_id, user_id, listing_id, amount, payment_method, payment_details, status, receipt_number)
    VALUES 
    ('PAY-RE-2026-8801', 2, 1, 500, 'UPI / Google Pay', 'aarav@okhdfcbank', 'Success', 'REC-2026-0901')
    """)

    cursor.execute("""
    INSERT INTO notifications (user_id, title, message, channel, recipient_contact, status)
    VALUES 
    (2, 'Token Advance Received', 'Your token deposit of ₹500 for Sunrise Executive PG was verified. Receipt #REC-2026-0901 generated.', 'WhatsApp', '+91 98421 11223', 'Delivered'),
    (2, 'Visit Appointment Confirmed', 'Host confirmed your in-person visit slot for Sep 20 at 04:30 PM.', 'Email', 'student@ksrct.ac.in', 'Delivered')
    """)

    conn.commit()


def seed_images_and_payments(cursor, conn):
    """Updates existing records with image URLs and sample payments if not present."""
    galleries = {
        1: [
            "/static/images/rooms/sunrise_pg.jpg"
        ],
        2: [
            "/static/images/rooms/maple_residency.jpg"
        ],
        3: [
            "/static/images/rooms/nest_girls_pg.jpg"
        ],
        4: [
            "/static/images/rooms/anna_residency.jpg"
        ],
        5: [
            "/static/images/rooms/greenfield_suites.jpg"
        ],
        6: [
            "/static/images/rooms/emerald_living.jpg"
        ]
    }

    for lid, imgs in galleries.items():
        cursor.execute("UPDATE listings SET image_url = ?, images = ? WHERE id = ?", (imgs[0], json.dumps(imgs), lid))

    cursor.execute("SELECT COUNT(*) FROM payments")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO payments (payment_id, user_id, listing_id, amount, payment_method, payment_details, status, receipt_number)
        VALUES 
        ('PAY-RE-2026-8801', 2, 1, 500, 'UPI / Google Pay', 'aarav@okhdfcbank', 'Success', 'REC-2026-0901')
        """)

    cursor.execute("SELECT COUNT(*) FROM notifications")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO notifications (user_id, title, message, channel, recipient_contact, status)
        VALUES 
        (2, 'Token Advance Received', 'Your token deposit of ₹500 for Sunrise Executive PG was verified. Receipt #REC-2026-0901 generated.', 'WhatsApp', '+91 98421 11223', 'Delivered'),
        (2, 'Visit Appointment Confirmed', 'Host confirmed your in-person visit slot for Sep 20 at 04:30 PM.', 'Email', 'student@ksrct.ac.in', 'Delivered')
        """)

    conn.commit()
