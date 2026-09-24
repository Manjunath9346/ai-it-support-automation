import json
import re

import httpx

from app.config import settings
from app.utils.validators import validate_category, validate_priority


def fallback_analysis(title: str, description: str) -> dict:
    """
    Simple fallback classification used when an LLM API is not configured.
    This keeps local development functional.
    """

    text = f"{title} {description}".lower()

    if any(word in text for word in [
        "vpn",
        "internet",
        "network",
        "wifi",
        "connection",
    ]):
        category = "Network"

    elif any(word in text for word in [
        "laptop",
        "computer",
        "keyboard",
        "mouse",
        "monitor",
        "printer",
    ]):
        category = "Hardware"

    elif any(word in text for word in [
        "password",
        "login",
        "account",
        "access",
        "permission",
    ]):
        category = "Access"

    elif any(word in text for word in [
        "virus",
        "malware",
        "suspicious",
        "phishing",
        "security",
    ]):
        category = "Security"

    elif any(word in text for word in [
        "application",
        "software",
        "program",
        "application error",
    ]):
        category = "Software"

    else:
        category = "Other"

    if category == "Security":
        priority = "CRITICAL"

    elif any(word in text for word in [
        "not working",
        "urgent",
        "cannot",
        "can't",
        "failed",
        "down",
    ]):
        priority = "HIGH"

    else:
        priority = "MEDIUM"

    summary = description[:300]

    suggested_response = (
        "Thank you for reporting this issue. "
        "Your ticket has been received and is being reviewed by the IT support team."
    )

    return {
        "category": category,
        "priority": priority,
        "summary": summary,
        "suggested_response": suggested_response,
    }


async def analyze_ticket(
    title: str,
    description: str,
) -> dict:

    if not settings.llm_enabled:
        return fallback_analysis(title, description)

    prompt = f"""
You are an IT support ticket classification assistant.

Analyze the following support ticket.

Title:
{title}

Description:
{description}

Return ONLY valid JSON using exactly this structure:

{{
    "category": "Hardware|Software|Network|Access|Security|Other",
    "priority": "LOW|MEDIUM|HIGH|CRITICAL",
    "summary": "short summary",
    "suggested_response": "professional response to the user"
}}

Rules:
- Security incidents should normally be HIGH or CRITICAL.
- Do not invent facts.
- Keep the summary concise.
- The response should be professional and useful.
"""

    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.llm_model,
        "messages": [
            {
                "role": "system",
                "content": "You classify IT support tickets and return valid JSON.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.2,
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                settings.llm_api_url,
                headers=headers,
                json=payload,
            )

        response.raise_for_status()

        data = response.json()

        content = data["choices"][0]["message"]["content"]

        # Remove accidental markdown code fences.
        content = re.sub(
            r"```json|```",
            "",
            content,
            flags=re.IGNORECASE,
        ).strip()

        result = json.loads(content)

        category = validate_category(
            str(result.get("category", "Other"))
        )

        priority = validate_priority(
            str(result.get("priority", "MEDIUM"))
        )

        summary = str(
            result.get("summary", "")
        ).strip()

        suggested_response = str(
            result.get("suggested_response", "")
        ).strip()

        if not summary:
            raise ValueError("AI summary is empty")

        if not suggested_response:
            raise ValueError("AI response is empty")

        return {
            "category": category,
            "priority": priority,
            "summary": summary,
            "suggested_response": suggested_response,
        }

    except Exception:
        # Keep the system operational if the external AI service fails.
        return fallback_analysis(title, description)