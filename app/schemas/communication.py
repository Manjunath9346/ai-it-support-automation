from datetime import datetime

from pydantic import BaseModel, Field


class ChatMessageCreate(BaseModel):
    message: str = Field(min_length=1, max_length=5000)


class ChatMessageResponse(BaseModel):
    id: int
    ticket_id: str
    sender_email: str
    sender_name: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


class MeetingCreate(BaseModel):
    scheduled_at: datetime


class MeetingResponse(BaseModel):
    id: int
    ticket_id: str
    employee_email: str
    resolver_email: str
    scheduled_at: datetime
    status: str
    room_id: str
    created_at: datetime

    class Config:
        from_attributes = True