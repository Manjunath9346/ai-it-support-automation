VALID_CATEGORIES = {
    "Hardware",
    "Software",
    "Network",
    "Access",
    "Security",
    "Other",
}

VALID_PRIORITIES = {
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
}

VALID_STATUSES = {
    "OPEN",
    "IN_PROGRESS",
    "RESOLVED",
    "CLOSED",
    "ESCALATED",
}


def validate_category(category: str) -> str:
    if category not in VALID_CATEGORIES:
        return "Other"

    return category


def validate_priority(priority: str) -> str:
    priority = priority.upper()

    if priority not in VALID_PRIORITIES:
        return "MEDIUM"

    return priority


def validate_status(status: str) -> str:
    status = status.upper()

    if status not in VALID_STATUSES:
        raise ValueError("Invalid ticket status")

    return status