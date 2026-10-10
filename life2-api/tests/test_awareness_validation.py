import pytest
from fastapi import HTTPException

from app.awareness.router import _validate_question_response


def test_valid_awareness_response():
    _validate_question_response("AWR_Q01_RETIREMENT_AGE", "CONFIRMED")


def test_unknown_question_rejected():
    with pytest.raises(HTTPException) as exc:
        _validate_question_response("NOPE", "CONFIRMED")
    assert exc.value.status_code == 404


def test_not_applicable_rejected_when_not_in_question_options():
    with pytest.raises(HTTPException) as exc:
        _validate_question_response("AWR_Q01_RETIREMENT_AGE", "NOT_APPLICABLE")
    assert exc.value.status_code == 422
