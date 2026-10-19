"""Load DUMMY sample data into students.db (all names/contacts are fictional)."""
from app import crud
from app.database import connect, init_db

SAMPLES = [
    {"name": "Asha Rao", "date_of_birth": "2004-05-17", "email": "asha.rao@example.com",
     "phone": "+91 90000 00001", "course": "Python Backend", "enrollment_date": "2024-07-01"},
    {"name": "Ravi Kumar", "date_of_birth": "2006-02-11", "email": "ravi.kumar@example.com",
     "course": "Data Science", "enrollment_date": "2024-07-01"},
    {"name": "Meena Iyer", "date_of_birth": "2005-09-30", "email": "meena.iyer@example.com",
     "phone": "+91 90000 00003", "course": "Python Backend", "enrollment_date": "2024-08-15"},
    {"name": "Arjun Reddy", "date_of_birth": "2003-12-25", "phone": "+91 90000 00004",
     "course": "Web Development", "enrollment_date": "2023-07-10"},
    {"name": "Sneha Patel", "date_of_birth": "2007-03-08", "email": "sneha.patel@example.com",
     "course": "Data Science", "enrollment_date": "2025-01-05"},
]

if __name__ == "__main__":
    init_db()
    db = connect()
    existing = crud.count_students(db)
    if existing:
        print(f"Database already has {existing} students; skipping seed.")
    else:
        for s in SAMPLES:
            crud.create_student(db, s)
        print(f"Inserted {len(SAMPLES)} dummy students.")
    db.close()
