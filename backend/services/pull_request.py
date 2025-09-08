from sqlmodel import select, Session
from models import PullRequest, Repository, PRState
from core.database import engine
from typing import List


def upsert_pr(
    repo: Repository, number: int, state: PRState, text: str, embedding: List[float]
) -> PullRequest:
    """
    Create or update a pull request
    """
    with Session(engine) as session:
        pr = session.exec(
            select(PullRequest).where(
                PullRequest.repo_id == repo.id, PullRequest.number == number
            )
        ).one_or_none()

        if pr:
            pr.state = state
            pr.text = text
            pr.embedding = embedding
        else:
            pr = PullRequest(
                repo_id=repo.id,
                number=number,
                state=state,
                text=text,
                embedding=embedding,
            )

        session.add(pr)
        session.commit()
        session.refresh(pr)
        return pr
