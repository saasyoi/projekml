import pytest
from pydantic import ValidationError

from api.schemas import QuizFinish, RegisterRequest


def test_quiz_finish_valid():
    qf = QuizFinish(topic="apk", level="dasar", correct_count=2, total=3)
    assert qf.correct_count == 2


def test_quiz_finish_rejects_zero_total():
    with pytest.raises(ValidationError):
        QuizFinish(topic="apk", level="dasar", correct_count=0, total=0)


def test_quiz_finish_rejects_correct_count_above_total():
    with pytest.raises(ValidationError):
        QuizFinish(topic="apk", level="dasar", correct_count=5, total=3)


def test_quiz_finish_rejects_negative_correct_count():
    with pytest.raises(ValidationError):
        QuizFinish(topic="apk", level="dasar", correct_count=-1, total=3)


def test_register_request_rejects_blank_name():
    with pytest.raises(ValidationError):
        RegisterRequest(email="a@example.com", name="   ", password="password123")


def test_register_request_rejects_short_password():
    with pytest.raises(ValidationError):
        RegisterRequest(email="a@example.com", name="Budi", password="short")


def test_register_request_rejects_invalid_email():
    with pytest.raises(ValidationError):
        RegisterRequest(email="not-an-email", name="Budi", password="password123")


def test_register_request_valid():
    req = RegisterRequest(email="Budi@Example.com", name=" Budi ", password="password123")
    assert req.name == "Budi"
