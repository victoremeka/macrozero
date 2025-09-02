import os
import dotenv
from sqlmodel import create_engine, Session
from sqlalchemy.engine import URL
from .models import *

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

def add_review(repo_id: int, commit_id: int, review: str):
    with Session(engine) as session:
        session.add(
            Review(
                repo_id=repo_id,
                commit_id=commit_id,
                review=review
            )
        )
        session.commit()
    
def add_commit(id: int, hash: str, message: str):
    with Session(engine) as session:
        session.add(
            Commit(
                id=id,
                hash=hash,
                message=message,
            )
        )
        session.commit()

def add_repository(id: int, name: str, owner: int):
    with Session(engine) as session:
        session.add(
            Repository(
                id=id,
                name=name,
                owner=owner,
            )
        )
        session.commit()

def add_user(id: int, name: str, email: str, org: str):
    with Session(engine) as session:
        session.add(
            User(
                id=id,
                name=name,
                email=email,
                org=org
            )
        )
        session.commit()

def main():
    create_db_and_tables()

if __name__ == "__main__":
    main()