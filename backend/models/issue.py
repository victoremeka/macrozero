from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, Enum, UniqueConstraint
from typing import List

from .enums import IssueState
from .repository import Repository
from .pull_request import PullRequest


class Issue(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    repo_id: int = Field(foreign_key="repository.id", index=True)
    number: int = Field(index=True)
    state: IssueState = Field(
        sa_column=Column(Enum(IssueState, name="issue_state")), default=IssueState.OPEN
    )

    # optional association if a PR closes this issue
    pr_id: int | None = Field(default=None, foreign_key="pullrequest.id", index=True)

    repo: Repository = Relationship(back_populates="issues")
    pr: PullRequest = Relationship(back_populates="issues")
    files: List["IssueFile"] = Relationship(back_populates="issue")

    __table_args__ = (
        UniqueConstraint("repo_id", "number", name="uq_issue_repo_number"),
    )


class IssueFile(SQLModel, table=True):
    issue_id: int = Field(foreign_key="issue.id", primary_key=True)
    file_path: str = Field(primary_key=True, index=True)
    touches: int = Field(default=1)

    issue: Issue = Relationship(back_populates="files")
