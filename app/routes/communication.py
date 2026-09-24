from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.ticket import Ticket
from app.models.communication import ChatMessage, Meeting
from app.schemas.communication import (
    ChatMessageCreate,
    ChatMessageResponse,
    MeetingCreate,
    MeetingResponse,
)
from app.auth import get_current_user


router = APIRouter(
    prefix="/api/communication",
    tags=["Communication"],
)


def get_ticket_for_user(
    ticket_id: str,
    current_user,
    db: Session,
):
    ticket = (
        db.query(Ticket)
        .filter(Ticket.ticket_id == ticket_id)
        .first()
    )

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    allowed = False

    if current_user.role == "ADMIN":
        allowed = True

    elif current_user.role == "EMPLOYEE":
        allowed = (
            ticket.user_email.lower()
            == current_user.email.lower()
        )

    elif current_user.role == "RESOLVER":
        allowed = (
            ticket.assigned_to
            and ticket.assigned_to.lower()
            == current_user.email.lower()
        )

    if not allowed:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to access this ticket communication",
        )

    return ticket


# ============================================================
# CHAT
# ============================================================

@router.get(
    "/tickets/{ticket_id}/messages",
    response_model=list[ChatMessageResponse],
)
def get_messages(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    get_ticket_for_user(ticket_id, current_user, db)

    return (
        db.query(ChatMessage)
        .filter(ChatMessage.ticket_id == ticket_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )


@router.post(
    "/tickets/{ticket_id}/messages",
    response_model=ChatMessageResponse,
)
def send_message(
    ticket_id: str,
    data: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    get_ticket_for_user(ticket_id, current_user, db)

    message = ChatMessage(
        ticket_id=ticket_id,
        sender_email=current_user.email,
        sender_name=current_user.name,
        message=data.message.strip(),
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message


# ============================================================
# MEETINGS
# ============================================================

@router.post(
    "/tickets/{ticket_id}/meetings",
    response_model=MeetingResponse,
)
def create_meeting(
    ticket_id: str,
    data: MeetingCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ticket = get_ticket_for_user(
        ticket_id,
        current_user,
        db,
    )

    if not ticket.assigned_to:
        raise HTTPException(
            status_code=400,
            detail="Ticket is not assigned to a resolver",
        )

    if current_user.role == "EMPLOYEE":
        employee_email = current_user.email
        resolver_email = ticket.assigned_to

    elif current_user.role == "RESOLVER":
        employee_email = ticket.user_email
        resolver_email = current_user.email

    else:
        employee_email = ticket.user_email
        resolver_email = ticket.assigned_to

    scheduled_at = data.scheduled_at

    if scheduled_at.tzinfo is not None:
        scheduled_at = scheduled_at.astimezone(timezone.utc).replace(tzinfo=None)

    if scheduled_at <= datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail="Meeting time must be in the future",
        )

    meeting = Meeting(
        ticket_id=ticket_id,
        employee_email=employee_email,
        resolver_email=resolver_email,
        scheduled_at=scheduled_at,
        status="REQUESTED",
        room_id=f"support-{uuid4().hex[:12]}",
    )

    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    return meeting


@router.get(
    "/tickets/{ticket_id}/meetings",
    response_model=list[MeetingResponse],
)
def get_meetings(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    get_ticket_for_user(ticket_id, current_user, db)

    return (
        db.query(Meeting)
        .filter(Meeting.ticket_id == ticket_id)
        .order_by(Meeting.scheduled_at.asc())
        .all()
    )


@router.patch(
    "/meetings/{meeting_id}/accept",
    response_model=MeetingResponse,
)
def accept_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    meeting = (
        db.query(Meeting)
        .filter(Meeting.id == meeting_id)
        .first()
    )

    if not meeting:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found",
        )

    if (
        current_user.email.lower()
        != meeting.resolver_email.lower()
    ):
        raise HTTPException(
            status_code=403,
            detail="Only the assigned resolver can accept this meeting",
        )

    meeting.status = "ACCEPTED"

    db.commit()
    db.refresh(meeting)

    return meeting


@router.patch(
    "/meetings/{meeting_id}/cancel",
    response_model=MeetingResponse,
)
def cancel_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    meeting = (
        db.query(Meeting)
        .filter(Meeting.id == meeting_id)
        .first()
    )

    if not meeting:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found",
        )

    if current_user.email.lower() not in [
        meeting.employee_email.lower(),
        meeting.resolver_email.lower(),
    ]:
        raise HTTPException(
            status_code=403,
            detail="You are not part of this meeting",
        )

    meeting.status = "CANCELLED"

    db.commit()
    db.refresh(meeting)

    return meeting