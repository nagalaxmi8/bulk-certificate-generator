
from app.schemas.job import JobCreate

request_data = {
    "event_name": "Python Workshop",
    "recipients": [
        {"name": "Ravi Kumar", "email": "ravi@example.com"}
    ]
}

job = JobCreate(**request_data)
print("Validation successful!")
print(job.model_dump())
