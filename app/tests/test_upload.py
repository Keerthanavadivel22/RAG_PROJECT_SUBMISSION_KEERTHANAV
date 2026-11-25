
import pytest

from database.db import get_connection
from main import app


@pytest.fixture
def authenticated_client():

    from fastapi.testclient import TestClient
    from utils.auth import get_current_user

    app.dependency_overrides[get_current_user] = lambda: {
        "user_id": 1,
        "email": "test@example.com"
    }

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


# 1. Unsupported file
def test_upload_unsupported_file(authenticated_client):

    response = authenticated_client.post(
        "/upload/document",
        files={
            "file": (
                "sample.xlsx",
                b"Some content",
                "application/octet-stream"
            )
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Only PDF, DOCX and TXT files are allowed"
    )


# 2. Empty file
def test_upload_empty_file(authenticated_client):

    response = authenticated_client.post(
        "/upload/document",
        files={
            "file": (
                "empty.txt",
                b"",
                "text/plain"
            )
        }
    )

    assert response.status_code == 400


# 3. Invalid PDF
def test_upload_invalid_pdf(authenticated_client):

    response = authenticated_client.post(
        "/upload/document",
        files={
            "file": (
                "invalid.pdf",
                b"This is not a PDF",
                "application/pdf"
            )
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid PDF file"


# 4. Invalid DOCX
def test_upload_invalid_docx(authenticated_client):

    response = authenticated_client.post(
        "/upload/document",
        files={
            "file": (
                "invalid.docx",
                b"This is not a DOCX",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid DOCX file"


# 5. Invalid UTF-8 TXT
def test_upload_invalid_txt_encoding(authenticated_client):

    response = authenticated_client.post(
        "/upload/document",
        files={
            "file": (
                "invalid.txt",
                b"\xff\xfe\xfa",
                "text/plain"
            )
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Text file must use UTF-8 encoding"
    )


# 6. Upload without authentication
def test_upload_without_authentication():

    from fastapi.testclient import TestClient

    client = TestClient(app)

    response = client.post(
        "/upload/document",
        files={
            "file": (
                "sample.txt",
                b"Python content",
                "text/plain"
            )
        }
    )

    assert response.status_code == 401
