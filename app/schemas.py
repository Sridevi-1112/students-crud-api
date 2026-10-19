"""Pydantic models: request validation and response shapes."""
import re
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?[0-9\s\-()]{7,20}$")


class _StudentFields(BaseModel):
    @field_validator("email", check_fields=False)
    @classmethod
    def _check_email(cls, v):
        if v is None:
            return v
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("invalid email address")
        return v

    @field_validator("phone", check_fields=False)
    @classmethod
    def _check_phone(cls, v):
        if v is None:
            return v
        v = v.strip()
        if not PHONE_RE.match(v):
            raise ValueError("invalid phone number (7-20 digits, may start with +)")
        return v

    @field_validator("date_of_birth", check_fields=False)
    @classmethod
    def _check_dob(cls, v):
        if v is not None and v >= date.today():
            raise ValueError("date_of_birth must be in the past")
        return v


class StudentCreate(_StudentFields):
    name: str = Field(..., min_length=1, max_length=100, examples=["Asha Rao"])
    date_of_birth: date = Field(..., examples=["2004-05-17"])
    email: Optional[str] = Field(None, examples=["asha.rao@example.com"])
    phone: Optional[str] = Field(None, examples=["+91 90000 00001"])
    course: Optional[str] = Field(None, max_length=100, examples=["Python Backend"])
    address: Optional[str] = Field(None, max_length=300)
    enrollment_date: Optional[date] = None

    @field_validator("name")
    @classmethod
    def _strip_name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("name must not be blank")
        return v

    @model_validator(mode="after")
    def _need_contact(self):
        if not self.email and not self.phone:
            raise ValueError("provide at least one contact: email and/or phone")
        return self


class StudentUpdate(_StudentFields):
    """All fields optional (used by PATCH)."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    course: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=300)
    enrollment_date: Optional[date] = None


class StudentOut(BaseModel):
    id: int
    name: str
    date_of_birth: date
    email: Optional[str] = None
    phone: Optional[str] = None
    course: Optional[str] = None
    address: Optional[str] = None
    enrollment_date: Optional[date] = None


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500,
                          examples=["How many students are there?"])


class AskResponse(BaseModel):
    question: str
    answer: str
    records_used: int
