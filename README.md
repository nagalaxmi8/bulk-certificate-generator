# Bulk Certificate Generator

## 1. Overview

Bulk Certificate Generator is a web-based application built using Python, FastAPI, and PostgreSQL. It accepts multiple recipients in a single API request, generates individual PDF participation certificates using a predefined template, tracks generation progress, and allows users to retrieve generated certificates.

The application handles each recipient independently so that a failure while generating one certificate does not prevent the remaining recipients from being processed.

## 2. Technologies Used

- **Python** — application logic
- **FastAPI** — REST API development
- **PostgreSQL** — relational database
- **SQLAlchemy** — database operations and ORM
- **Pydantic** — request validation
- **ReportLab** — PDF certificate generation
- **HTML, CSS, JavaScript** — frontend interface
- **Pytest** — automated testing
- **HTTPX** — API testing

## 3. Features

- Create a bulk certificate-generation job.
- Validate event and recipient details, including email addresses.
- Generate an individual PDF certificate for each recipient.
- Track job status, total recipients, successful and failed certificates, and progress.
- Continue processing other recipients when an individual certificate fails.
- Retrieve certificate details and download generated PDF files.
- Display generation progress and certificate download options through a web interface.
- Test API endpoints, validation, certificate generation, and failure scenarios.

## 4. Project Structure

```text
bulk-certificate-generator/
├── app/
│   ├── core/
│   │   └── config.py
│   ├── database/
│   │   ├── connection.py
│   │   └── base.py
│   ├── models/
│   │   ├── job.py
│   │   ├── certificate.py
│   │   └── __init__.py
│   ├── schemas/
│   │   └── job.py
│   ├── services/
│   │   ├── pdf_generator.py
│   │   └── job_processor.py
│   └── main.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── storage/
│   └── certificates/
├── tests/
│   └── test_api.py
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── check_db.py
└── check_schema.py
```

## 5. Setup and Installation

### Prerequisites

- Python 3.12 or a compatible version
- PostgreSQL
- pip

### Step 1: Clone or open the project

Open the project directory in your terminal:

```cmd
cd bulk-certificate-generator
```

### Step 2: Create and activate a virtual environment

On Windows:

```cmd
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install dependencies

```cmd
pip install -r requirements.txt
```

### Step 4: Configure the database

1. Ensure PostgreSQL is installed and running.
2. Create a database named `certificate_db`.
3. Copy `.env.example` to `.env`.
4. Update the database connection string in `.env` with your PostgreSQL credentials and database details.

Keep `.env` private and never commit database passwords or other secrets.

## 6. Run the Application

The backend and frontend must run in separate terminals.

### Start the backend

From the project root, with the virtual environment activated:

```cmd
uvicorn app.main:app --reload
```

Backend URL:

`http://127.0.0.1:8000`

Interactive API documentation:

`http://127.0.0.1:8000/docs`

### Start the frontend

Open a second terminal in the project root and run:

```cmd
python -m http.server 5500 --directory frontend
```

Open the frontend:

`http://127.0.0.1:5500/`

## 7. API Usage

### Create a bulk generation job

**Method:** `POST`

**Endpoint:** `/api/jobs`

Example request body:

```json
{
  "event_name": "Python Workshop 2026",
  "recipients": [
    {
      "name": "Ananya Sharma",
      "email": "ananya@example.com"
    },
    {
      "name": "Rahul Reddy",
      "email": "rahul@example.com"
    }
  ]
}
```

The API validates the request, creates a generation job, and returns a job identifier and initial job details.

### Check job status and progress

**Method:** `GET`

**Endpoint:** `/api/jobs/{job_id}`

Returns job information, including the total number of recipients, successful and failed certificate counts, status, and progress.

### List certificates for a job

**Method:** `GET`

**Endpoint:** `/api/jobs/{job_id}/certificates`

Returns certificate records associated with the specified job, including their generation statuses.

### Download a certificate

**Method:** `GET`

**Endpoint:** `/api/certificates/{certificate_id}`

Returns the generated PDF when the requested certificate is available.

## 8. Job and Certificate Processing

Each bulk request creates a job containing individual certificate records.

The application processes recipients separately and records the outcome of each certificate.

Certificate statuses include:

- `PENDING` — generation has not yet completed.
- `GENERATED` — the PDF was generated successfully.
- `FAILED` — certificate generation failed.

The job tracks overall progress and successful and failed counts. Depending on the processing outcome, a job can finish with a completed, failed, or completed-with-errors status.

## 9. Run Tests

From the project root, execute:

```cmd
python -m pytest -v
```

The automated test suite covers:

- API availability and job creation
- Invalid email and missing or invalid request data
- Empty recipient lists and whitespace-only values
- Missing jobs and certificates
- Certificate listing and PDF retrieval
- Certificates that are not yet ready for download
- Missing generated PDF files
- Partial and complete certificate-generation failures

The current test suite contains 16 tests, which have passed in the development environment.

## 10. Design Decisions

- **FastAPI:** Provides REST endpoints, request handling, validation integration, and interactive API documentation.
- **PostgreSQL:** Stores job information and individual certificate records in relational tables.
- **SQLAlchemy:** Manages database models and database operations.
- **Pydantic:** Validates incoming request data before processing.
- **ReportLab:** Generates PDF certificates using a predefined layout.
- **Per-recipient error handling:** Prevents an individual certificate failure from stopping the remaining recipients.
- **Job tracking:** Allows users to inspect generation status, progress, and results.
- **Separate frontend and backend:** Keeps the user interface independent of the API implementation.

## 11. Limitations and Future Improvements

- Background processing currently runs within the FastAPI application process; it does not use a separate durable task queue.
- Email delivery and automated certificate distribution are not implemented.
- The application currently uses a predefined certificate template.

Possible future improvements include a durable background task queue, configurable certificate templates, email delivery, authentication, and deployment to a cloud platform.

