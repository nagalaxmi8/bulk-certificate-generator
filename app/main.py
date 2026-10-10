
from pathlib import Path

from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.base import Base
from app.database.connection import engine, get_db
from app.models import GenerationJob, Certificate
from app.schemas.job import JobCreate
from app.services.job_processor import process_job
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Bulk Certificate Generator API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
@app.get("/")
def root():
    return {"message": "API is running"}


@app.post("/api/jobs", status_code=201)
def create_job(
    request: JobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    job = GenerationJob(
        event_name=request.event_name,
        total_count=len(request.recipients)
    )

    db.add(job)
    db.flush()

    for recipient in request.recipients:
        certificate = Certificate(
            job_id=job.id,
            recipient_name=recipient.name,
            recipient_email=str(recipient.email)
        )
        db.add(certificate)

    db.commit()
    db.refresh(job)

    background_tasks.add_task(process_job, job.id)

    return {
        "job_id": job.id,
        "event_name": job.event_name,
        "status": job.status,
        "total_count": job.total_count
    }


@app.get("/api/jobs/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(GenerationJob).filter_by(id=job_id).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    return {
        "job_id": job.id,
        "event_name": job.event_name,
        "status": job.status,
        "total_count": job.total_count,
        "success_count": job.success_count,
        "failure_count": job.failure_count,
        "progress_percent": round(
            (job.success_count + job.failure_count)
            / job.total_count * 100, 2
        ) if job.total_count else 0
    }


@app.get("/api/jobs/{job_id}/certificates")
def get_job_certificates(
    job_id: int,
    db: Session = Depends(get_db)
):
    job = db.query(GenerationJob).filter_by(id=job_id).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    certificates = db.query(Certificate).filter_by(
        job_id=job_id
    ).all()

    return [
        {
            "certificate_id": cert.id,
            "recipient_name": cert.recipient_name,
            "recipient_email": cert.recipient_email,
            "status": cert.status,
            "error_message": cert.error_message
        }
        for cert in certificates
    ]


@app.get("/api/certificates/{certificate_id}")
def download_certificate(
    certificate_id: int,
    db: Session = Depends(get_db)
):
    certificate = db.query(Certificate).filter_by(
        id=certificate_id
    ).first()

    if not certificate:
        raise HTTPException(
            status_code=404,
            detail="Certificate not found"
        )

    if certificate.status != "GENERATED" or not certificate.file_path:
        raise HTTPException(
            status_code=409,
            detail="Certificate is not ready for download"
        )

    file_path = Path(certificate.file_path)

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Certificate file not found"
        )

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=file_path.name
    )
