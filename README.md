# RentEase

Student PG/room rental and roommate-matching platform — Python full-stack project.

Currently included: the **Home page** only. More pages (listings, roommate matcher,
booking, auth, admin) will be added as separate routes/templates as the project grows.

## Setup

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5000/** in your browser.

## Project structure

```
rentease/
├── app.py                  # Flask app + routes
├── requirements.txt
├── templates/
│   ├── base.html           # shared <head>, fonts, layout shell
│   └── home.html           # home page content
└── static/
    ├── css/style.css       # all styling
    └── js/                 # empty for now — reserved for future pages
```

## Next steps

- Listings page with search/filter
- Roommate matcher form + scoring logic
- Booking/visit-request flow
- Auth (student / owner / admin roles)
- Database models (PostgreSQL/MySQL via SQLAlchemy)
