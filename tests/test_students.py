import os
import tempfile

import pytest
from fastapi.testclient import TestClient

# Use a throwaway database for tests
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["STUDENTS_DB"] = _tmp.name

from app import database  # noqa: E402
from app.main import app  # noqa: E402

database.DB_PATH = _tmp.name


@pytest.fixture()
def client():
    database.init_db()
    conn = database.connect()
    conn.execute("DELETE FROM students")
    conn.commit()
    conn.close()
    with TestClient(app) as c:
        yield c


def make(**over):
    base = {"name": "Test User", "date_of_birth": "2004-01-01", "email": "test@example.com"}
    base.update(over)
    return base


def test_create_and_get(client):
    r = client.post("/students", json=make(course="Python"))
    assert r.status_code == 201
    sid = r.json()["id"]
    assert client.get(f"/students/{sid}").json()["course"] == "Python"


def test_list_and_filters(client):
    client.post("/students", json=make(name="Old One", date_of_birth="2000-01-01", email="a@x.com"))
    client.post("/students", json=make(name="Young One", date_of_birth="2007-06-01", email="b@x.com"))
    assert len(client.get("/students").json()) == 2
    assert len(client.get("/students?born_after=2005-01-01").json()) == 1
    assert client.get("/students?name=Young").json()[0]["name"] == "Young One"


def test_put_and_patch(client):
    sid = client.post("/students", json=make()).json()["id"]
    r = client.patch(f"/students/{sid}", json={"course": "Data Science"})
    assert r.status_code == 200 and r.json()["course"] == "Data Science"
    assert r.json()["name"] == "Test User"  # untouched
    r = client.put(f"/students/{sid}", json=make(name="Renamed"))
    assert r.json()["name"] == "Renamed"


def test_delete(client):
    sid = client.post("/students", json=make()).json()["id"]
    assert client.delete(f"/students/{sid}").status_code == 204
    assert client.get(f"/students/{sid}").status_code == 404


def test_missing_record_404(client):
    assert client.get("/students/999").status_code == 404
    assert client.patch("/students/999", json={"name": "X"}).status_code == 404
    assert client.put("/students/999", json=make()).status_code == 404
    assert client.delete("/students/999").status_code == 404


def test_validation(client):
    assert client.post("/students", json=make(email="not-an-email")).status_code == 422
    assert client.post("/students", json=make(date_of_birth="2999-01-01")).status_code == 422
    assert client.post("/students", json={"name": "No Contact", "date_of_birth": "2004-01-01"}).status_code == 422
    assert client.post("/students", json=make(name="  ")).status_code == 422


def test_duplicate_email_409(client):
    client.post("/students", json=make())
    assert client.post("/students", json=make(name="Other")).status_code == 409


def test_persistence(client):
    sid = client.post("/students", json=make()).json()["id"]
    conn = database.connect()
    row = conn.execute("SELECT name FROM students WHERE id=?", (sid,)).fetchone()
    conn.close()
    assert row["name"] == "Test User"


def test_ai_context_retrieval(client):
    from app import ai
    client.post("/students", json=make(name="Old", date_of_birth="2000-01-01", email="a@x.com"))
    client.post("/students", json=make(name="New", date_of_birth="2006-01-01", email="b@x.com"))
    conn = database.connect()
    rows, _ = ai.retrieve_context(conn, "List students born after 2005")
    conn.close()
    assert [r["name"] for r in rows] == ["New"]
