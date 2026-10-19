"""Optional bonus: natural-language questions answered by a local Ollama model.

Safety design: the model NEVER writes or runs SQL. The backend picks a fixed,
parameterised query from a few recognised patterns, fetches the matching
records, and gives them to the model purely as context.
"""
import os
import re
import sqlite3

import httpx

from . import crud

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
MAX_CONTEXT_RECORDS = 50

_BORN_RE = re.compile(r"born\s+(after|before|in)\s+(\d{4})", re.I)


def retrieve_context(db: sqlite3.Connection, question: str) -> tuple[list[dict], str]:
    """Return (records, description of what was retrieved)."""
    q = question.lower()
    m = _BORN_RE.search(q)
    if m:
        word, year = m.group(1), int(m.group(2))
        if word == "after":      # born after year X  -> dob >= (X+1)-01-01
            rows = crud.list_students(db, born_after=f"{year}-12-31", limit=MAX_CONTEXT_RECORDS)
            return rows, f"students born after {year}"
        if word == "before":
            rows = crud.list_students(db, born_before=f"{year}-01-01", limit=MAX_CONTEXT_RECORDS)
            return rows, f"students born before {year}"
        rows = crud.list_students(db, born_after=f"{year - 1}-12-31",
                                  born_before=f"{year + 1}-01-01", limit=MAX_CONTEXT_RECORDS)
        return rows, f"students born in {year}"

    course = re.search(r"(?:in|enrolled in|taking)\s+(?:the\s+)?([\w .+#-]+?)\s*(?:course)?\s*[?.!]*$", q)
    if course and "course" in q:
        rows = crud.list_students(db, course=course.group(1).strip(), limit=MAX_CONTEXT_RECORDS)
        return rows, f"students whose course matches '{course.group(1).strip()}'"

    rows = crud.list_students(db, limit=MAX_CONTEXT_RECORDS)
    return rows, "all students (up to 50)"


def build_prompt(question: str, records: list[dict], description: str, total: int) -> str:
    lines = [
        f"- id={r['id']}, name={r['name']}, dob={r['date_of_birth']}, "
        f"course={r['course'] or 'n/a'}, email={r['email'] or 'n/a'}"
        for r in records
    ]
    return (
        "You answer questions about a student database using ONLY the data below. "
        "If the data does not contain the answer, say you don't know. Be brief.\n\n"
        f"Total students in database: {total}\n"
        f"Records retrieved ({description}): {len(records)}\n"
        + ("\n".join(lines) if lines else "(no matching records)")
        + f"\n\nQuestion: {question}\nAnswer:"
    )


def ask_ollama(prompt: str) -> str:
    resp = httpx.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False,
              "options": {"temperature": 0}},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json().get("response", "").strip()
