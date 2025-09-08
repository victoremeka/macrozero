from sqlmodel import select, Session
from models import Repository
from core.database import engine


def upsert_repo(gh_id: int, owner: str) -> Repository:
    """
    Create or update a repository
    """
    with Session(engine) as session:
        repo = session.exec(
            select(Repository).where(Repository.gh_id == gh_id)
        ).one_or_none()
        if repo:
            repo.owner = owner
        else:
            repo = Repository(owner=owner, gh_id=gh_id)

        session.add(repo)
        session.commit()
        session.refresh(repo)
        return repo
