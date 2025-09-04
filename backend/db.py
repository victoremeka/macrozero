import os
import dotenv
from sqlmodel import create_engine, Session, select
from sqlalchemy.engine import URL
from backend.models import *

# dotenv.load_dotenv()

# db_host = os.getenv("DB_HOST")
# db_username = os.getenv("DB_USERNAME")
# db_password = os.getenv("DB_PASSWORD")
# db_database = os.getenv("DB_DATABASE")
# db_port = os.getenv("DB_PORT")
# if not db_port is None:
#     db_port = int(db_port)

# ca_path = os.path.abspath("isrgrootx1.pem")

# def get_db_engine():
#     connect_args = {}
#     if ca_path:
#         connect_args = {
#             "ssl_verify_cert": True,
#             "ssl_verify_identity": True,
#             "ssl_ca": ca_path,
#         }
#     return create_engine(
#         URL.create(
#             drivername="mysql+pymysql",
#             username=db_username,
#             password=db_password,
#             host=db_host,
#             port=db_port, # type: ignore
#             database=db_database,
#         ),
#         connect_args=connect_args,
#         echo=True # reminder: take out in prod
#     )

# engine = get_db_engine()

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)

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
    
def add_commit(hash: str, repo_id: int, owner_id: int, message: str):
    with Session(engine) as session:
        session.add(
            Commit(
                hash=hash,
                repo_id=repo_id,
                owner_id=owner_id,
                message=message,
            )
        )
        session.commit()

def add_repository(name: str):
    with Session(engine) as session:
        session.add(
            Repository(
                name=name,
            )
        )
        session.commit()

def add_user(name: str, email: str, org: str | None = None):
    with Session(engine) as session:
        user = session.add(
            User(
                name=name,
                email=email,
                org=org
            )
        )
        session.commit()

def get_review(repo_id: int, commit_id:int):
    with Session(engine) as session:
        results = session.exec(select(Review).where(Review.repo_id == repo_id, Review.commit_id == commit_id)).all()
        return results

def get_commit(hash: str) -> Commit | None:
    pass

def get_user(id: int) -> User | None:
    with Session(engine) as session:
        user = session.get(User, id)
        return user

def get_repository(id: int) -> Repository | None:
    with Session(engine) as session:
        repo = session.get(Repository, id)
        return repo

def main():
    create_db_and_tables()
    user = get_user(1)
    repo = get_repository(1)
    if not (user and repo) is None:
        add_commit(
            hash="pl00h",
            repo_id=repo.id,
            owner_id=user.id,
            message="woah, this works"
        )
    

if __name__ == "__main__":
    main()