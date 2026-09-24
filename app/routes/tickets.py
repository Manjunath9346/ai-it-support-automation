from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.ticket import Ticket
from app.schemas.ticket import (
    TicketCreate,
    TicketResponse,
    TicketStatusUpdate,
)
from app.services.ai_service import analyze_ticket
from app.services.notification_service import send_escalation_notification
from app.utils.validators import validate_status

from app.auth import (
    get_current_user,
    employee_only,
    resolver_or_admin,
    admin_only,
    User,
    AuthSessionLocal,
)


router = APIRouter(
    prefix="/api/tickets",
    tags=["Tickets"],
)


def generate_ticket_id() -> str:
    return f"TKT-{uuid4().hex[:8].upper()}"


# ============================================================
# CREATE TICKET
# EMPLOYEE ONLY
# ============================================================

@router.post(
    "",
    response_model=TicketResponse,
    status_code=201,
)
def create_ticket(
    ticket_data: TicketCreate,
    db: Session = Depends(get_db),
    current_user=Depends(employee_only),
):
    ticket = Ticket(
        ticket_id=generate_ticket_id(),
        user_name=current_user.name,
        user_email=current_user.email,
        issue_title=ticket_data.issue_title,
        issue_description=ticket_data.issue_description,
        category="Other",
        priority="MEDIUM",
        status="OPEN",
        ai_processed=0,
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return ticket


# ============================================================
# GET TICKETS
# EMPLOYEE / RESOLVER / ADMIN
# ============================================================

@router.get(
    "",
    response_model=list[TicketResponse],
)
def get_tickets(
    db: Session = Depends(get_db),
    search: str | None = Query(default=None),
    status: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    category: str | None = Query(default=None),
    current_user=Depends(get_current_user),
):

    # EMPLOYEE
    # Only their own tickets
    if current_user.role == "EMPLOYEE":

        query = db.query(Ticket).filter(
            Ticket.user_email == current_user.email
        )

    # RESOLVER
    # Only tickets assigned to this resolver
    elif current_user.role == "RESOLVER":

        query = db.query(Ticket).filter(
            Ticket.assigned_to == current_user.email
        )

    # ADMIN
    # All tickets
    else:

        query = db.query(Ticket)

    # SEARCH
    if search:

        search_term = f"%{search}%"

        query = query.filter(
            (Ticket.ticket_id.ilike(search_term))
            | (Ticket.issue_title.ilike(search_term))
            | (Ticket.issue_description.ilike(search_term))
            | (Ticket.user_name.ilike(search_term))
        )

    # STATUS
    if status:

        query = query.filter(
            Ticket.status == status.upper()
        )

    # PRIORITY
    if priority:

        query = query.filter(
            Ticket.priority == priority.upper()
        )

    # CATEGORY
    if category:

        query = query.filter(
            Ticket.category == category
        )

    return query.order_by(
        Ticket.created_at.desc()
    ).all()


# ============================================================
# PENDING TICKETS
# N8N / AUTOMATION
# ============================================================

@router.get(
    "/pending",
    response_model=list[TicketResponse],
)
def get_pending_tickets(
    db: Session = Depends(get_db),
):
    """
    Used by n8n to find new tickets that have not
    yet been processed by AI.
    """

    return (
        db.query(Ticket)
        .filter(Ticket.ai_processed == 0)
        .filter(Ticket.status == "OPEN")
        .order_by(Ticket.created_at.asc())
        .limit(20)
        .all()
    )


# ============================================================
# TICKET STATS
# RESOLVER / ADMIN
# ============================================================

@router.get(
    "/stats",
)
def get_ticket_stats(
    db: Session = Depends(get_db),
    current_user=Depends(resolver_or_admin),
):

    # Resolver statistics should only contain
    # tickets assigned to that resolver.
    if current_user.role == "RESOLVER":

        base_query = db.query(Ticket).filter(
            Ticket.assigned_to == current_user.email
        )

    else:

        base_query = db.query(Ticket)

    total = base_query.with_entities(
        func.count(Ticket.id)
    ).scalar() or 0

    open_count = base_query.filter(
        Ticket.status == "OPEN"
    ).count()

    in_progress = base_query.filter(
        Ticket.status == "IN_PROGRESS"
    ).count()

    resolved = base_query.filter(
        Ticket.status == "RESOLVED"
    ).count()

    closed = base_query.filter(
        Ticket.status == "CLOSED"
    ).count()

    escalated = base_query.filter(
        Ticket.status == "ESCALATED"
    ).count()

    high_priority = base_query.filter(
        Ticket.priority.in_(["HIGH", "CRITICAL"])
    ).count()

    critical = base_query.filter(
        Ticket.priority == "CRITICAL"
    ).count()

    return {
        "total": total,
        "open": open_count,
        "in_progress": in_progress,
        "resolved": resolved,
        "closed": closed,
        "escalated": escalated,
        "high_priority": high_priority,
        "critical": critical,
    }


# ============================================================
# GET SINGLE TICKET
# ============================================================

@router.get(
    "/{ticket_id}",
    response_model=TicketResponse,
)
def get_ticket(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
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

    # EMPLOYEE
    if (
        current_user.role == "EMPLOYEE"
        and ticket.user_email.lower()
        != current_user.email.lower()
    ):

        raise HTTPException(
            status_code=403,
            detail="You can only access your own tickets",
        )

    # RESOLVER
    if (
        current_user.role == "RESOLVER"
        and (
            ticket.assigned_to is None
            or ticket.assigned_to.lower()
            != current_user.email.lower()
        )
    ):

        raise HTTPException(
            status_code=403,
            detail="This ticket is not assigned to you",
        )

    return ticket


# ============================================================
# AI ANALYSIS
# RESOLVER / ADMIN
# ============================================================

@router.post(
    "/{ticket_id}/analyze",
    response_model=TicketResponse,
)
async def analyze_ticket_endpoint(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(resolver_or_admin),
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

    # Resolver can analyze only their assigned ticket
    if (
        current_user.role == "RESOLVER"
        and (
            ticket.assigned_to is None
            or ticket.assigned_to.lower()
            != current_user.email.lower()
        )
    ):

        raise HTTPException(
            status_code=403,
            detail="This ticket is not assigned to you",
        )

    result = await analyze_ticket(
        title=ticket.issue_title,
        description=ticket.issue_description,
    )

    ticket.category = result["category"]
    ticket.priority = result["priority"]
    ticket.ai_summary = result["summary"]
    ticket.ai_response = result["suggested_response"]
    ticket.ai_processed = 1
    ticket.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(ticket)

    return ticket


# ============================================================
# UPDATE STATUS
# RESOLVER / ADMIN
# ============================================================

@router.patch(
    "/{ticket_id}/status",
    response_model=TicketResponse,
)
def update_ticket_status(
    ticket_id: str,
    status_data: TicketStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(resolver_or_admin),
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

    # Resolver can modify only their assigned tickets
    if (
        current_user.role == "RESOLVER"
        and (
            ticket.assigned_to is None
            or ticket.assigned_to.lower()
            != current_user.email.lower()
        )
    ):

        raise HTTPException(
            status_code=403,
            detail="This ticket is not assigned to you",
        )

    try:

        new_status = validate_status(
            status_data.status
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    ticket.status = new_status
    ticket.updated_at = datetime.utcnow()

    # START WORK
    if new_status == "IN_PROGRESS":

        if current_user.role == "RESOLVER":

            ticket.assigned_to = current_user.email

            if ticket.assigned_at is None:

                ticket.assigned_at = datetime.utcnow()

    # RESOLVE TICKET
    if new_status == "RESOLVED":

        ticket.resolved_at = datetime.utcnow()
        ticket.resolved_by = current_user.email

        if status_data.resolution_notes:

            ticket.resolution_notes = (
                status_data.resolution_notes
            )

        # Safety fallback
        if ticket.assigned_to is None:

            ticket.assigned_to = current_user.email
            ticket.assigned_at = datetime.utcnow()

    # REOPEN TICKET
    if new_status in ["OPEN", "IN_PROGRESS"]:

        ticket.resolved_at = None
        ticket.resolved_by = None

    db.commit()
    db.refresh(ticket)

    return ticket


# ============================================================
# ESCALATE
# RESOLVER / ADMIN
# ============================================================

@router.post(
    "/{ticket_id}/escalate",
    response_model=TicketResponse,
)
def escalate_ticket(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(resolver_or_admin),
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

    # Resolver can escalate only their ticket
    if (
        current_user.role == "RESOLVER"
        and (
            ticket.assigned_to is None
            or ticket.assigned_to.lower()
            != current_user.email.lower()
        )
    ):

        raise HTTPException(
            status_code=403,
            detail="This ticket is not assigned to you",
        )

    ticket.status = "ESCALATED"
    ticket.updated_at = datetime.utcnow()

    # Keep the resolver who escalated it as the owner
    if current_user.role == "RESOLVER":

        ticket.assigned_to = current_user.email

        if ticket.assigned_at is None:

            ticket.assigned_at = datetime.utcnow()

    db.commit()

    send_escalation_notification(
        ticket_id=ticket.ticket_id,
        issue_title=ticket.issue_title,
        priority=ticket.priority,
    )

    db.refresh(ticket)

    return ticket


# ============================================================
# ADMIN - MANUAL TICKET ASSIGNMENT
# ============================================================

class AssignTicketRequest(BaseModel):
    assigned_to: str


@router.patch(
    "/{ticket_id}/assign",
    response_model=TicketResponse,
)
def assign_ticket(
    ticket_id: str,
    data: AssignTicketRequest,
    db: Session = Depends(get_db),
    current_user=Depends(admin_only),
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

    resolver_email = (
        data.assigned_to.strip().lower()
    )

    auth_db = AuthSessionLocal()

    try:

        resolver = (
            auth_db.query(User)
            .filter(
                User.email == resolver_email,
                User.role == "RESOLVER",
            )
            .first()
        )

        if not resolver:

            raise HTTPException(
                status_code=400,
                detail="Resolver not found",
            )

    finally:

        auth_db.close()

    ticket.assigned_to = resolver_email
    ticket.assigned_at = datetime.utcnow()
    ticket.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(ticket)

    return ticket


# ============================================================
# N8N - SAVE AI RESULT
# ============================================================

class AIResultRequest(BaseModel):
    category: str
    priority: str
    ai_summary: str
    ai_response: str


@router.patch(
    "/{ticket_id}/ai-result",
    response_model=TicketResponse,
)
def update_ai_result(
    ticket_id: str,
    data: AIResultRequest,
    db: Session = Depends(get_db),
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

    ticket.category = data.category
    ticket.priority = data.priority
    ticket.ai_summary = data.ai_summary
    ticket.ai_response = data.ai_response
    ticket.ai_processed = 1
    ticket.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(ticket)

    return ticket


# ============================================================
# N8N - AUTOMATIC ASSIGNMENT
# ============================================================

@router.post(
    "/{ticket_id}/auto-assign",
    response_model=TicketResponse,
)
def auto_assign_ticket(
    ticket_id: str,
    db: Session = Depends(get_db),
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

    # Don't overwrite an existing assignment
    if ticket.assigned_to:

        return ticket

    auth_db = AuthSessionLocal()

    try:

        resolvers = (
            auth_db.query(User)
            .filter(User.role == "RESOLVER")
            .all()
        )

        if not resolvers:

            raise HTTPException(
                status_code=400,
                detail="No resolver available",
            )

        # Find resolver with the fewest active tickets
        resolver_loads = {}

        for resolver in resolvers:

            active_count = (
                db.query(Ticket)
                .filter(
                    Ticket.assigned_to == resolver.email,
                    Ticket.status.in_(
                        [
                            "OPEN",
                            "IN_PROGRESS",
                            "ESCALATED",
                        ]
                    ),
                )
                .count()
            )

            resolver_loads[resolver.email] = active_count

        resolver = min(
            resolvers,
            key=lambda r: resolver_loads[r.email],
        )

        ticket.assigned_to = resolver.email
        ticket.assigned_at = datetime.utcnow()
        ticket.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(ticket)

        return ticket

    finally:

        auth_db.close()