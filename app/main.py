"""Students Database CRUD API (FastAPI + SQLite) with optional Ollama Q&A."""
import sqlite3
from contextlib import asynccontextmanager
from datetime import date
from typing import Optional

import httpx
from fastapi import Depends, FastAPI, HTTPException, Query, Response, status

from . import ai, crud
from .database import get_db, init_db
from .schemas import AskRequest, AskResponse, StudentCreate, StudentOut, StudentUpdate


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Students Database API",
    description="CRUD API for student records. FastAPI + SQLite. Optional local-AI endpoint via Ollama.",
    version="1.0.0",
    lifespan=lifespan,
)


def _not_found(student_id: int) -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, f"Student {student_id} not found")


def _conflict() -> HTTPException:
    return HTTPException(status.HTTP_409_CONFLICT, "A student with this email already exists")


@app.get("/", tags=["health"])
def root():
    return {"message": "Students API is running", "docs": "/docs"}


# ---------- CREATE ----------
@app.post("/students", response_model=StudentOut, status_code=status.HTTP_201_CREATED, tags=["students"])
def create_student(student: StudentCreate, db: sqlite3.Connection = Depends(get_db)):
    try:
        return crud.create_student(db, student.model_dump())
    except sqlite3.IntegrityError:
        raise _conflict()


# ---------- READ (list / filter) ----------
@app.get("/students", response_model=list[StudentOut], tags=["students"])
def list_students(
    name: Optional[str] = Query(None, description="Substring match on name"),
    course: Optional[str] = Query(None, description="Substring match on course"),
    born_after: Optional[date] = Query(None, description="Date of birth strictly after (YYYY-MM-DD)"),
    born_before: Optional[date] = Query(None, description="Date of birth strictly before (YYYY-MM-DD)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: sqlite3.Connection = Depends(get_db),
):
    return crud.list_students(
        db, name, course,
        born_after.isoformat() if born_after else None,
        born_before.isoformat() if born_before else None,
        skip, limit,
    )


# ---------- READ (one) ----------
@app.get("/students/{student_id}", response_model=StudentOut, tags=["students"])
def get_student(student_id: int, db: sqlite3.Connection = Depends(get_db)):
    student = crud.get_student(db, student_id)
    if not student:
        raise _not_found(student_id)
    return student


# ---------- UPDATE (full replace) ----------
@app.put("/students/{student_id}", response_model=StudentOut, tags=["students"])
def replace_student(student_id: int, student: StudentCreate, db: sqlite3.Connection = Depends(get_db)):
    try:
        updated = crud.update_student(db, student_id, student.model_dump())
    except sqlite3.IntegrityError:
        raise _conflict()
    if not updated:
        raise _not_found(student_id)
    return updated


# ---------- UPDATE (partial) ----------
@app.patch("/students/{student_id}", response_model=StudentOut, tags=["students"])
def patch_student(student_id: int, changes: StudentUpdate, db: sqlite3.Connection = Depends(get_db)):
    data = changes.model_dump(exclude_unset=True)
    for required in ("name", "date_of_birth"):
        if required in data and data[required] is None:
            raise HTTPException(422, f"{required} cannot be null")
    current = crud.get_student(db, student_id)
    if not current:
        raise _not_found(student_id)
    merged = {**current, **data}
    if not merged.get("email") and not merged.get("phone"):
        raise HTTPException(422, "Student must keep at least one contact (email or phone)")
    try:
        return crud.update_student(db, student_id, data)
    except sqlite3.IntegrityError:
        raise _conflict()


# ---------- DELETE ----------
@app.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["students"])
def delete_student(student_id: int, db: sqlite3.Connection = Depends(get_db)):
    if not crud.delete_student(db, student_id):
        raise _not_found(student_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- OPTIONAL BONUS: local AI ----------
@app.post("/ai/ask", response_model=AskResponse, tags=["ai (optional)"])
def ask(body: AskRequest, db: sqlite3.Connection = Depends(get_db)):
    """Ask a natural-language question. The backend retrieves records; the model only reads them."""
    records, description = ai.retrieve_context(db, body.question)
    prompt = ai.build_prompt(body.question, records, description, crud.count_students(db))
    try:
        answer = ai.ask_ollama(prompt)
    except (httpx.HTTPError, OSError):
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            f"Ollama is not reachable at {ai.OLLAMA_URL}. Start it and run: ollama pull {ai.OLLAMA_MODEL}",
        )
    return AskResponse(question=body.question, answer=answer, records_used=len(records))
