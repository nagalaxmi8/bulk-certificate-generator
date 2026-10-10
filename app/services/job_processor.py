
from app.database.connection import SessionLocal
from app.models import GenerationJob, Certificate
from app.services.pdf_generator import generate_certificate


def process_job(job_id: int):
    db = SessionLocal()

    try:
        job = db.query(GenerationJob).filter_by(id=job_id).first()

        if not job:
            return

        job.status = "PROCESSING"
        db.commit()

        certificate_ids = [
            cert.id
            for cert in db.query(Certificate).filter_by(job_id=job_id).all()
        ]

        for certificate_id in certificate_ids:
            certificate = db.query(Certificate).filter_by(
                id=certificate_id
            ).first()

            try:
                certificate.status = "PROCESSING"
                db.commit()

                file_path = generate_certificate(
                    name=certificate.recipient_name,
                    event_name=job.event_name,
                    certificate_id=certificate.id
                )

                certificate.file_path = file_path
                certificate.status = "GENERATED"
                certificate.error_message = None
                db.commit()

            except Exception as error:
                db.rollback()

                certificate = db.query(Certificate).filter_by(
                    id=certificate_id
                ).first()

                if certificate:
                    certificate.status = "FAILED"
                    certificate.error_message = str(error)[:1000]
                    db.commit()

        certificates = db.query(Certificate).filter_by(
            job_id=job_id
        ).all()

        job = db.query(GenerationJob).filter_by(id=job_id).first()
        job.success_count = sum(
            cert.status == "GENERATED" for cert in certificates
        )
        job.failure_count = sum(
            cert.status == "FAILED" for cert in certificates
        )

        if job.failure_count == 0:
            job.status = "COMPLETED"
        elif job.success_count == 0:
            job.status = "FAILED"
        else:
            job.status = "COMPLETED_WITH_ERRORS"

        db.commit()

    finally:
        db.close()
