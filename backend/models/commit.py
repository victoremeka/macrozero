from datetime import datetime, timezone
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, UniqueConstraint
from typing import List

from .repository import Repository
from .pull_request import PullRequest, CommitPullRequestLink, EMBED_DIM

from tidb_vector.sqlalchemy import VectorType

class Commit(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    repo_id: int = Field(foreign_key="repository.id", index=True)
    sha: str = Field(index=True)
    message: str
    author_login: str | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    diff_text_raw: str
    diff_text_embedding: List[float] = Field(
        sa_column=Column(VectorType(EMBED_DIM), nullable=False)
    )

    repo: Repository = Relationship(back_populates="commits")
    prs: list[PullRequest] = Relationship(
        back_populates="commits", link_model=CommitPullRequestLink
    )

    __tablename__ = "git_commit"  # type: ignore
    __table_args__ = (UniqueConstraint("repo_id", "sha", name="uq_commit_repo_sha"),)
