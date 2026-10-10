
from pydantic import BaseModel, EmailStr, Field


class RecipientInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr


class JobCreate(BaseModel):
    event_name: str = Field(min_length=1, max_length=200)
    recipients: list[RecipientInput] = Field(min_length=1)
from pydantic import BaseModel, EmailStr, Field, field_validator


class RecipientInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Recipient name cannot be blank")
        return value


class JobCreate(BaseModel):
    event_name: str = Field(min_length=1, max_length=200)
    recipients: list[RecipientInput] = Field(min_length=1)

    @field_validator("event_name")
    @classmethod
    def validate_event_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Event name cannot be blank")
        return value
