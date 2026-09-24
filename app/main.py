from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine

# Import models so SQLAlchemy knows about them.
from app.models import Ticket

from app.routes import health, tickets
from app.auth import router as auth_router

from app.models.communication import ChatMessage, Meeting
from app.routes import communication



import jwt

from app.auth import (
    JWT_SECRET,
    JWT_ALGORITHM,
    AuthSessionLocal,
    User,
)


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title=settings.app_name,
    description="AI-powered IT support ticket automation system",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    communication.router
)

app.include_router(
    health.router
)

app.include_router(
    tickets.router
)

app.include_router(auth_router, prefix="/api")




# ============================================================
# REAL-TIME CALL SIGNALING
# ============================================================

active_call_connections = {}


async def send_to_user(email, message):

    connections = active_call_connections.get(
        email.lower(),
        set()
    )

    dead_connections = set()

    for connection in connections:

        try:
            await connection.send_json(message)

        except Exception:
            dead_connections.add(connection)

    for connection in dead_connections:
        connections.discard(connection)


@app.websocket("/ws/call")
async def call_websocket(
    websocket: WebSocket,
    token: str
):

    try:

        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )

        user_id = payload.get("sub")

        if not user_id:
            await websocket.close(code=1008)
            return

        db = AuthSessionLocal()

        try:

            user = (
                db.query(User)
                .filter(User.id == int(user_id))
                .first()
            )

        finally:

            db.close()

        if not user:
            await websocket.close(code=1008)
            return

        email = user.email.lower()

    except Exception:

        await websocket.close(code=1008)
        return


    await websocket.accept()


    active_call_connections.setdefault(
        email,
        set()
    ).add(websocket)


    try:

        await websocket.send_json({
            "type": "connected"
        })


        while True:

            message = await websocket.receive_json()

            target = message.get("to")

            if target:

                await send_to_user(
                    target,
                    {
                        **message,
                        "from": email
                    }
                )


    except WebSocketDisconnect:

        pass

    finally:

        connections = active_call_connections.get(
            email,
            set()
        )

        connections.discard(websocket)

        if not connections:
            active_call_connections.pop(
                email,
                None
            )





@app.get("/")
def root():
    return {
        "message": "AI IT Support Automation API",
        "status": "running",
    }