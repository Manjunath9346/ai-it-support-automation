from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TicketCreate(BaseModel):
    issue_title: str = Field(min_length=3, max_length=255)
    issue_description: str = Field(min_length=5)


class TicketStatusUpdate(BaseModel):
    status: str
    resolution_notes: str | None = None

class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticket_id: str
    user_name: str
    user_email: str
    issue_title: str
    issue_description: str

    category: str
    priority: str
    status: str

    ai_summary: str | None
    ai_response: str | None

    ai_processed: bool

    assigned_to: str | None
    assigned_at: datetime | None

    resolved_by: str | None
    resolution_notes: str | None

    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None