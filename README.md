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

Employee / Resolver / Admin
            │
            ▼
     Azure Static Web Apps
            │
            ▼
       FastAPI Backend
            │
      ┌─────┴─────┐
      ▼           ▼
 Aiven MySQL    REST APIs
                    │
                    ▼
                   n8n
                    │
                    ▼
              Google Gemini
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
       Category   Priority   Summary
          │         │         │
          └─────────┼─────────┘
                    ▼
             Auto Assignment
                    │
                    ▼
                Resolver

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

## Resume Project Entry

### SupportFlow – AI-Powered IT Support Ticket Automation
Python, FastAPI, MySQL, n8n, Google Gemini, REST APIs, Azure

- Developed an AI-powered IT support platform with separate Employee, Resolver, and Admin workflows for managing support tickets.
- Automated ticket classification, priority detection, summarization, suggested responses, and resolver assignment using Google Gemini and n8n.
- Built REST APIs using FastAPI, SQLAlchemy, and MySQL with JWT-based role authentication and ticket lifecycle management.
- Implemented employee–resolver communication, meeting scheduling, and real-time voice/video support.
- Deployed the frontend and backend on Microsoft Azure with MySQL hosted on Aiven.

## One-Minute Interview Explanation

I developed a project called SupportFlow, which is an AI-powered IT support ticket automation system.

The system has three roles: Employee, Resolver, and Admin. Employees can create IT support tickets, while resolvers handle and resolve assigned tickets.

The main feature is the automation workflow. When an employee creates a ticket, the ticket is stored in MySQL. n8n periodically checks for unprocessed tickets and sends the ticket information to Google Gemini. Gemini determines the category and priority and generates a short summary and suggested response.

The results are then sent back to my FastAPI backend, and the system automatically assigns the ticket to an available resolver.

I built the backend using Python and FastAPI, used SQLAlchemy for database operations, MySQL for persistence, n8n for workflow automation, and Google Gemini for AI processing. The application is deployed using Microsoft Azure.

## If the Interviewer Asks: "Why did you use n8n?"

I used n8n to separate the automation workflow from the core backend. Instead of putting the entire AI processing flow inside FastAPI, n8n handles the scheduled ticket processing, communication with the AI model, and updating the ticket through REST APIs. This also makes the workflow easier to modify.

## If the Interviewer Asks: "Why FastAPI?"

FastAPI provides a lightweight way to build REST APIs in Python. It also provides automatic API documentation through Swagger UI and works well with Pydantic validation and SQLAlchemy.

## If the Interviewer Asks: "Where is AI actually used?"

AI is used when a new ticket needs to be analyzed. Gemini receives the ticket title and description and returns structured information containing the category, priority, summary, and suggested response. The backend then stores those results with the ticket.

## If the Interviewer Asks: "What was your contribution?"

I designed and implemented the application architecture, backend APIs, database models, authentication and role management, ticket workflow, n8n automation, Gemini integration, communication features, frontend dashboards, and deployment.