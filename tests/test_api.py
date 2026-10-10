
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.database.connection import get_db
from app.services import job_processor


client = TestClient(app)


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "API is running"


def test_invalid_email():
    response = client.post(
        "/api/jobs",
        json={
            "event_name": "Python Workshop",
            "recipients": [
                {"name": "Ravi Kumar", "email": "invalid-email"}
            ],
        },
    )

    assert response.status_code == 422


def test_missing_job():
    response = client.get("/api/jobs/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"


def test_create_job():
    response = client.post(
        "/api/jobs",
        json={
            "event_name": "Test Workshop",
            "recipients": [
                {"name": "Test User", "email": "test@example.com"}
            ],
        },
    )

    assert response.status_code == 201
    assert response.json()["total_count"] == 1
    assert "job_id" in response.json()


def test_job_certificates():
    response = client.post(
        "/api/jobs",
        json={
            "event_name": "PDF Test Workshop",
            "recipients": [
                {
                    "name": "PDF Test User",
                    "email": "pdf-test@example.com",
                }
            ],
        },
    )

    assert response.status_code == 201
    job_id = response.json()["job_id"]

    certificates_response = client.get(
        f"/api/jobs/{job_id}/certificates"
    )

    assert certificates_response.status_code == 200
    assert len(certificates_response.json()) == 1


def test_certificate_download():
    response = client.post(
        "/api/jobs",
        json={
            "event_name": "Download Test",
            "recipients": [
                {
                    "name": "Download User",
                    "email": "download@example.com",
                }
            ],
        },
    )

    assert response.status_code == 201
    job_id = response.json()["job_id"]

    certificates = client.get(
        f"/api/jobs/{job_id}/certificates"
    ).json()

    certificate_id = certificates[0]["certificate_id"]

    assert certificates[0]["status"] == "GENERATED"

    download_response = client.get(
        f"/api/certificates/{certificate_id}"
    )

    assert download_response.status_code == 200
    assert download_response.headers["content-type"] == "application/pdf"
    assert download_response.content.startswith(b"%PDF")


def test_partial_certificate_failure():
    original_generator = job_processor.generate_certificate

    def fail_first_certificate(name, event_name, certificate_id):
        if name == "Ravi Kumar":
            raise RuntimeError("Simulated PDF generation failure")

        return original_generator(name, event_name, certificate_id)

    with patch(
        "app.services.job_processor.generate_certificate",
        side_effect=fail_first_certificate,
    ):
        response = client.post(
            "/api/jobs",
            json={
                "event_name": "Failure Test Workshop",
                "recipients": [
                    {
                        "name": "Ravi Kumar",
                        "email": "ravi-fail@example.com",
                    },
                    {
                        "name": "Priya Sharma",
                        "email": "priya-pass@example.com",
                    },
                ],
            },
        )

    assert response.status_code == 201
    job_id = response.json()["job_id"]

    job_data = client.get(f"/api/jobs/{job_id}").json()

    assert job_data["status"] == "COMPLETED_WITH_ERRORS"
    assert job_data["success_count"] == 1
    assert job_data["failure_count"] == 1
    assert job_data["progress_percent"] == 100

    certificates = client.get(
        f"/api/jobs/{job_id}/certificates"
    ).json()

    statuses = {
        certificate["recipient_name"]: certificate["status"]
        for certificate in certificates
    }

    assert statuses["Ravi Kumar"] == "FAILED"
    assert statuses["Priya Sharma"] == "GENERATED"


def test_empty_recipient_list():
    response = client.post(
        "/api/jobs",
        json={
            "event_name": "Python Workshop",
            "recipients": [],
        },
    )

    assert response.status_code == 422


def test_whitespace_only_name_rejected():
    response = client.post(
        "/api/jobs",
        json={
            "event_name": "Python Workshop",
            "recipients": [
                {
                    "name": "   ",
                    "email": "test@example.com",
                }
            ],
        },
    )

    assert response.status_code == 422


def test_missing_certificate():
    response = client.get("/api/certificates/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Certificate not found"


def test_missing_pdf_file():
    response = client.post(
        "/api/jobs",
        json={
            "event_name": "Missing PDF Test",
            "recipients": [
                {
                    "name": "Test User",
                    "email": "missing-pdf@example.com",
                }
            ],
        },
    )

    assert response.status_code == 201
    job_id = response.json()["job_id"]

    certificates = client.get(
        f"/api/jobs/{job_id}/certificates"
    ).json()

    certificate_id = certificates[0]["certificate_id"]

    with patch("app.main.Path.is_file", return_value=False):
        download_response = client.get(
            f"/api/certificates/{certificate_id}"
        )

    assert download_response.status_code == 404
    assert download_response.json()["detail"] == "Certificate file not found"


def test_all_certificates_fail():
    with patch(
        "app.services.job_processor.generate_certificate",
        side_effect=RuntimeError("Simulated PDF failure"),
    ):
        response = client.post(
            "/api/jobs",
            json={
                "event_name": "All Failure Test",
                "recipients": [
                    {
                        "name": "User One",
                        "email": "user1@example.com",
                    },
                    {
                        "name": "User Two",
                        "email": "user2@example.com",
                    },
                ],
            },
        )

    assert response.status_code == 201
    job_id = response.json()["job_id"]

    job_data = client.get(f"/api/jobs/{job_id}").json()

    assert job_data["status"] == "FAILED"
    assert job_data["success_count"] == 0
    assert job_data["failure_count"] == 2
    assert job_data["progress_percent"] == 100

    certificates = client.get(
        f"/api/jobs/{job_id}/certificates"
    ).json()

    assert all(cert["status"] == "FAILED" for cert in certificates)


def test_download_certificate_not_ready():
    fake_certificate = MagicMock()
    fake_certificate.status = "PENDING"
    fake_certificate.file_path = None

    fake_query = MagicMock()
    fake_query.filter_by.return_value.first.return_value = fake_certificate

    fake_db = MagicMock()
    fake_db.query.return_value = fake_query

    app.dependency_overrides[get_db] = lambda: fake_db

    try:
        response = client.get("/api/certificates/12345")
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 409
    assert response.json()["detail"] == "Certificate is not ready for download"


def test_whitespace_only_event_name_rejected():
    response = client.post(
        "/api/jobs",
        json={
            "event_name": "   ",
            "recipients": [
                {
                    "name": "Test User",
                    "email": "event-test@example.com",
                }
            ],
        },
    )

    assert response.status_code == 422


def test_missing_recipients_field():
    response = client.post(
        "/api/jobs",
        json={"event_name": "Python Workshop"},
    )

    assert response.status_code == 422


def test_missing_job_certificate_list():
    response = client.get("/api/jobs/99999/certificates")

    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"
