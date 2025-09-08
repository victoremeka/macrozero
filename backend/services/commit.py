from sqlmodel import select, Session
from datetime import datetime, timezone
from models import Commit, Repository, PullRequest, CommitPullRequestLink
from core.database import engine
from typing import List, Optional


def upsert_commit(
    repo: Repository,
    sha: str,
    message: str,
    author_login: Optional[str],
    diff_text_raw: str,
    diff_embedding: List[float],
) -> Commit:
    """
    Create or update a commit
    """
    with Session(engine) as session:
        c = session.exec(
            select(Commit).where(Commit.repo_id == repo.id, Commit.sha == sha)
        ).one_or_none()

        if c:
            c.message = message
            c.author_login = author_login
            c.diff_text_raw = diff_text_raw
            c.diff_text_embedding = diff_embedding
        else:
            c = Commit(
                repo_id=repo.id,
                sha=sha,
                message=message,
                author_login=author_login,
                created_at=datetime.now(timezone.utc),
                diff_text_raw=diff_text_raw,
                diff_text_embedding=diff_embedding,
            )

        session.add(c)
        session.commit()
        session.refresh(c)
        return c


def link_commit_to_pr(commit: Commit, pr: PullRequest) -> None:
    """
    Link a commit to a pull request
    """
    with Session(engine) as session:
        session.flush()
        link = session.get(CommitPullRequestLink, (commit.id, pr.id))
        if not link:
            session.add(CommitPullRequestLink(commit_id=commit.id, pr_id=pr.id))
            session.commit()
