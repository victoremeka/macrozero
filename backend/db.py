import os
import dotenv
from sqlmodel import create_engine, Session, select
from sqlalchemy.engine import URL
from backend.models import *

dotenv.load_dotenv()

db_host = os.getenv("DB_HOST")
db_username = os.getenv("DB_USERNAME")
db_password = os.getenv("DB_PASSWORD")
db_database = os.getenv("DB_DATABASE")
db_port = os.getenv("DB_PORT")
if not db_port is None:
    db_port = int(db_port)

ca_path = os.path.abspath("isrgrootx1.pem")

def get_db_engine():
    connect_args = {}
    if ca_path:
        connect_args = {
            "ssl_verify_cert": True,
            "ssl_verify_identity": True,
            "ssl_ca": ca_path,
        }
    return create_engine(
        URL.create(
            drivername="mysql+pymysql",
            username=db_username,
            password=db_password,
            host=db_host,
            port=db_port, # type: ignore
            database=db_database,
        ),
        connect_args=connect_args,
        echo=True # reminder: take out in prod
    )

engine = get_db_engine()

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def main():
    create_db_and_tables()
    
if __name__ == "__main__":
    main()