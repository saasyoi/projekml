from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


# =====================================================================
# AUTH
# =====================================================================
class RegisterRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Nama tidak boleh kosong")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    total_score: int

    class Config:
        from_attributes = True


# =====================================================================
# QUIZ
# =====================================================================
class AnswerSubmission(BaseModel):
    topic: str
    level: str
    index: int
    letter: str


class QuizFinish(BaseModel):
    topic: str
    level: str
    correct_count: int
    total: int

    @field_validator("total")
    @classmethod
    def total_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("total harus lebih besar dari 0")
        return v

    @model_validator(mode="after")
    def correct_count_in_range(self):
        if self.correct_count < 0 or self.correct_count > self.total:
            raise ValueError("correct_count harus berada di antara 0 dan total")
        return self


class QuizAttemptOut(BaseModel):
    topic: str
    level: str
    score_percent: int
    passed: bool
    created_at: datetime

    class Config:
        from_attributes = True


# =====================================================================
# CHAT
# =====================================================================
class ChatMessageOut(BaseModel):
    role: str
    content: str
    has_image: bool
    status: str | None  # "danger" | "uncertain" | "no_content" | None
    created_at: datetime

    class Config:
        from_attributes = True
