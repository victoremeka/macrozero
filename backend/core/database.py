from sqlmodel import create_engine, Session, SQLModel
from sqlalchemy.engine import URL
import os
from pathlib import Path

from core.config import settings

# Get the absolute path to the CA certificate
ca_path = os.path.abspath("isrgrootx1.pem")


def get_db_engine():
    """
    Create and return a database engine based on settings
    """
    connect_args = {}
    if ca_path and Path(ca_path).exists():
        connect_args = {
            "ssl_verify_cert": True,
            "ssl_verify_identity": True,
            "ssl_ca": ca_path,
        }

    return create_engine(
        URL.create(
            drivername="mysql+pymysql",
            username=settings.db.username,
            password=settings.db.password,
            host=settings.db.host,
            port=settings.db.port,
            database=settings.db.database,
        ),
        connect_args=connect_args,
        echo=True,
    )


engine = get_db_engine()


def create_db_and_tables():
    """
    Create all database tables defined by SQLModel
    """
    SQLModel.metadata.create_all(engine)


def get_session():
    """
    Get a database session
    """
    with Session(engine) as session:
        yield session
