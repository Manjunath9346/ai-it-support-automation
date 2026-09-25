# SupportFlow – AI-Powered IT Support Ticket Automation

SupportFlow is an AI-powered IT support ticket management system that automates ticket classification, prioritization, summarization, suggested responses, and resolver assignment.

## Key Features

- Employee ticket creation and tracking
- AI-based ticket classification
- Automatic priority detection
- AI-generated ticket summaries
- AI-generated suggested responses
- Automatic resolver assignment
- Resolver ticket management
- Ticket status tracking
- Resolution notes
- Employee–Resolver chat
- Meeting scheduling
- Voice/video communication
- Role-based access control
- JWT authentication
- Admin user management
- Automated workflows using n8n

## Technology Stack

Frontend:
- HTML
- CSS
- JavaScript

Backend:
- Python
- FastAPI
- Pydantic
- SQLAlchemy

Database:
- MySQL
- Aiven

AI:
- Google Gemini

Automation:
- n8n

Authentication:
- JWT

Communication:
- REST APIs
- JSON
- WebSocket

Testing:
- Postman
- pytest

Version Control:
- Git
- GitHub

Deployment:
- Microsoft Azure

## System Architecture

```mermaid
flowchart TD
    U[Employee / Resolver / Admin] --> F[Azure Static Web Apps]
    F --> B[FastAPI Backend]
    B --> DB[Aiven MySQL]
    B --> N[n8n Automation]
    N --> G[Google Gemini AI]
    G --> C[Category]
    G --> P[Priority]
    G --> S[AI Summary]
    G --> R[Suggested Response]
    C --> A[Automatic Assignment]
    P --> A
    S --> A
    R --> A
    A --> RES[Resolver]


## Ticket Automation Flow

Employee creates ticket
        ↓
FastAPI
        ↓
MySQL
        ↓
n8n scheduled workflow
        ↓
Gemini analyzes ticket
        ↓
Category + Priority
+ Summary + Suggested Response
        ↓
FastAPI updates ticket
        ↓
Automatic resolver assignment
        ↓
Resolver handles ticket
        ↓
Resolution
        ↓
Employee receives update

## User Roles

### Employee

- Create tickets
- View own tickets
- Track ticket status
- Communicate with assigned resolver
- Schedule meetings
- View resolution details

### Resolver / IT Support Agent

- View assigned tickets
- Start working on tickets
- Communicate with employees
- Add resolution notes
- Resolve tickets
- Escalate tickets

### Admin

- Manage users
- Manage resolvers
- View all tickets
- Manage assignments
- Monitor the support platform

## Main Backend APIs

- POST /api/auth/login
- GET /api/auth/me
- POST /api/auth/setup-users
- GET /api/auth/users
- POST /api/auth/users
- DELETE /api/auth/users/{user_id}

- GET /health

- POST /api/tickets
- GET /api/tickets
- GET /api/tickets/pending
- GET /api/tickets/stats
- GET /api/tickets/{ticket_id}
- POST /api/tickets/{ticket_id}/analyze
- PATCH /api/tickets/{ticket_id}/status
- POST /api/tickets/{ticket_id}/escalate
- PATCH /api/tickets/{ticket_id}/assign
- PATCH /api/tickets/{ticket_id}/ai-result
- POST /api/tickets/{ticket_id}/auto-assign

- GET /api/tickets/{ticket_id}/messages
- POST /api/tickets/{ticket_id}/messages
- POST /api/tickets/{ticket_id}/meetings
- GET /api/tickets/{ticket_id}/meetings
- PATCH /api/meetings/{meeting_id}/accept
- PATCH /api/meetings/{meeting_id}/cancel

## AI Processing

When a new ticket is created, n8n detects the unprocessed ticket and sends its title and description to Google Gemini.

Gemini analyzes the ticket and returns:

- Category
- Priority
- AI summary
- Suggested response

The AI result is then sent back to the FastAPI backend and stored with the ticket.

## Why n8n?

n8n is used to separate the automation workflow from the core backend.

It handles:

- Detecting unprocessed tickets
- Sending ticket information to Gemini
- Processing the AI response
- Updating the ticket through REST APIs
- Triggering automatic assignment

This makes the automation workflow easier to modify without changing the main backend logic.

## Why FastAPI?

FastAPI was used to build the backend REST APIs because it provides:

- Lightweight Python API development
- Request validation with Pydantic
- Automatic Swagger API documentation
- Easy integration with SQLAlchemy
- Good support for asynchronous applications

## Why MySQL?

MySQL is used as the main relational database for storing:

- Users
- Tickets
- AI results
- Assignments
- Resolution information
- Chat messages
- Meetings

## Why Gemini?

Gemini is used for understanding the employee's IT support issue and generating structured AI results.

It performs:

- Ticket classification
- Priority detection
- Issue summarization
- Suggested response generation

## Deployment

Frontend:
https://black-rock-010714500.4.azurestaticapps.net

Backend:
https://supportflow-api-manju-2026-byh9esf5eefmgfch.indiasouthcentral-01.azurewebsites.net

Database:
Aiven MySQL
