# Students Database CRUD API

Internship project (EWB Edu Tech Pvt. Ltd. – Python Backend Development).
A backend application to manage student records with **FastAPI** and **SQLite**,
plus an **optional** local-AI endpoint powered by **Ollama**.

## Features

- Create, read (list / filter / single), update (PUT + PATCH) and delete students
- SQLite persistence (`students.db`, created automatically)
- Input validation (email, phone, date of birth, at least one contact) and clean error handling (404 / 409 / 422)
- Auto-generated interactive docs at `/docs`
- Optional bonus: ask natural-language questions about the data using a local Ollama model
- Automated tests (pytest)

## Project structure

```
students-crud-api/
├── app/
│   ├── main.py       # FastAPI routes
│   ├── schemas.py    # Pydantic validation models
│   ├── crud.py       # SQL operations (parameterised queries)
│   ├── database.py   # SQLite connection + table creation
│   └── ai.py         # Optional Ollama integration
├── tests/test_students.py
├── seed.py           # loads DUMMY sample data
├── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.10 or newer
- (Optional, for the AI bonus) [Ollama](https://ollama.com) installed

## Installation

```bash
git clone https://github.com/Sridevi-1112/students-crud-api.git
cd students-crud-api

python -m venv .venv
# Windows:  .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate

pip install -r requirements.txt
```

## Run

```bash
python seed.py                       # optional: load 5 dummy students
uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000/docs** to test every endpoint from the browser.

## Run the tests

```bash
pytest -q
```

## Student fields

| Field | Required | Notes |
|---|---|---|
| `id` | auto | unique, generated |
| `name` | yes | 1–100 chars |
| `date_of_birth` | yes | `YYYY-MM-DD`, must be in the past |
| `email` | email and/or phone | unique, validated |
| `phone` | email and/or phone | 7–20 digits, may start with `+` |
| `course` | no | |
| `address` | no | |
| `enrollment_date` | no | `YYYY-MM-DD` |

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/students` | Create a student |
| GET | `/students` | List / filter students |
| GET | `/students/{student_id}` | View a student |
| PUT | `/students/{student_id}` | Replace all details |
| PATCH | `/students/{student_id}` | Update some details |
| DELETE | `/students/{student_id}` | Delete a student |
| POST | `/ai/ask` | *(optional)* Ask a question using Ollama |

**List filters** (query params on `GET /students`): `name`, `course`, `born_after`, `born_before`, `skip`, `limit`.

### Sample requests (curl)

```bash
# Create
curl -X POST http://127.0.0.1:8000/students \
  -H "Content-Type: application/json" \
  -d '{"name":"Asha Rao","date_of_birth":"2004-05-17","email":"asha@example.com","course":"Python Backend"}'

# List all / filter
curl http://127.0.0.1:8000/students
curl "http://127.0.0.1:8000/students?born_after=2005-01-01"
curl "http://127.0.0.1:8000/students?course=Python"

# View one
curl http://127.0.0.1:8000/students/1

# Update (partial)
curl -X PATCH http://127.0.0.1:8000/students/1 \
  -H "Content-Type: application/json" -d '{"course":"Data Science"}'

# Delete
curl -X DELETE http://127.0.0.1:8000/students/1
```

### Error responses

| Status | When |
|---|---|
| 404 | Student ID does not exist |
| 409 | Email already used by another student |
| 422 | Invalid input (bad email/phone/date, missing contact, blank name) |

## Optional bonus: local AI with Ollama

1. Install Ollama and pull a small model:
   ```bash
   ollama pull llama3.2:1b
   ```
2. Make sure Ollama is running (default `http://localhost:11434`) and start the API.
3. Ask a question:
   ```bash
   curl -X POST http://127.0.0.1:8000/ai/ask \
     -H "Content-Type: application/json" \
     -d '{"question":"List students born after 2005"}'
   ```

**How it works (and why it's safe):** the model never writes or runs SQL. The
backend recognises the question pattern (e.g. "born after YEAR", a course name),
runs a fixed *parameterised* query, and passes only the retrieved records plus
the total student count to the model as context. The answer is therefore
grounded in real database rows. If Ollama isn't running, the endpoint returns a
clear `503` message and the rest of the API is unaffected.

Configuration via environment variables: `OLLAMA_URL`, `OLLAMA_MODEL`, `STUDENTS_DB`.

## Notes

- All sample data is **dummy** — no real student information is stored or published.
- `students.db` is git-ignored; no secrets are committed.
