from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import UniqueConstraint
from typing import List

from .commit import Commit
from .pull_request import PullRequest
from .issue import Issue


class Repository(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    owner: str
    gh_id: int = Field(index=True)

    commits: List["Commit"] = Relationship(back_populates="repo")
    prs: List["PullRequest"] = Relationship(back_populates="repo")
    issues: List["Issue"] = Relationship(back_populates="repo")

    __table_args__ = (UniqueConstraint("gh_id", name="uq_repo_gh_id"),)
