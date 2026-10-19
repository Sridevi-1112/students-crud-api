"""Database operations (all SQL is parameterised)."""
import sqlite3
from typing import Optional

COLUMNS = ["name", "date_of_birth", "email", "phone", "course", "address", "enrollment_date"]


def _to_db(data: dict) -> dict:
    """Convert date objects to ISO strings for SQLite."""
    return {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in data.items()}


def create_student(db: sqlite3.Connection, data: dict) -> dict:
    data = _to_db(data)
    cols = [c for c in COLUMNS if c in data]
    cur = db.execute(
        f"INSERT INTO students ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
        [data[c] for c in cols],
    )
    db.commit()
    return get_student(db, cur.lastrowid)


def get_student(db: sqlite3.Connection, student_id: int) -> Optional[dict]:
    row = db.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    return dict(row) if row else None


def list_students(
    db: sqlite3.Connection,
    name: Optional[str] = None,
    course: Optional[str] = None,
    born_after: Optional[str] = None,
    born_before: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[dict]:
    where, params = [], []
    if name:
        where.append("name LIKE ?")
        params.append(f"%{name}%")
    if course:
        where.append("course LIKE ?")
        params.append(f"%{course}%")
    if born_after:
        where.append("date_of_birth > ?")
        params.append(born_after)
    if born_before:
        where.append("date_of_birth < ?")
        params.append(born_before)
    sql = "SELECT * FROM students"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id LIMIT ? OFFSET ?"
    params += [limit, skip]
    return [dict(r) for r in db.execute(sql, params).fetchall()]


def count_students(db: sqlite3.Connection) -> int:
    return db.execute("SELECT COUNT(*) FROM students").fetchone()[0]


def update_student(db: sqlite3.Connection, student_id: int, data: dict) -> Optional[dict]:
    data = _to_db(data)
    cols = [c for c in COLUMNS if c in data]
    if cols:
        cur = db.execute(
            f"UPDATE students SET {', '.join(f'{c} = ?' for c in cols)} WHERE id = ?",
            [data[c] for c in cols] + [student_id],
        )
        db.commit()
        if cur.rowcount == 0:
            return None
    return get_student(db, student_id)


def delete_student(db: sqlite3.Connection, student_id: int) -> bool:
    cur = db.execute("DELETE FROM students WHERE id = ?", (student_id,))
    db.commit()
    return cur.rowcount > 0
