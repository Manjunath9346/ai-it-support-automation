from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings


connect_args = {}

if settings.aiven_ca_cert:
    cert_path = Path(settings.aiven_ca_cert)

    if not cert_path.is_absolute():
        cert_path = Path(__file__).resolve().parents[1] / cert_path

    connect_args = {
        "ssl": {
            "ca": str(cert_path)
        }
    }


engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=280,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()