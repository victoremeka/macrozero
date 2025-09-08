from datetime import datetime, timezone
import enum
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, Enum, UniqueConstraint
from typing import List

from .enums import PRState, IssueState
from .repository import Repository

# Define embedding dimensions
EMBED_DIM = 1536

from tidb_vector.sqlalchemy import VectorType
from .commit import Commit
from .issue import Issue



class CommitPullRequestLink(SQLModel, table=True):
    commit_id: int = Field(foreign_key="git_commit.id", primary_key=True)
    pr_id: int = Field(foreign_key="pullrequest.id", primary_key=True)


class PullRequest(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    repo_id: int = Field(foreign_key="repository.id", index=True)
    number: int = Field(index=True)
    state: PRState = Field(
        sa_column=Column(Enum(PRState, name="pr_state")), default=PRState.OPEN
    )

    text: str
    embedding: List[float] = Field(
        sa_column=Column(VectorType(EMBED_DIM), nullable=False),
    )

    commits: List["Commit"] = Relationship(
        back_populates="prs", link_model=CommitPullRequestLink
    )
    repo: Repository = Relationship(back_populates="prs")
    issues: List["Issue"] = Relationship(back_populates="pr")

    __table_args__ = (UniqueConstraint("repo_id", "number", name="uq_pr_repo_number"),)
