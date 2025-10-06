from datetime import datetime, timezone
import enum
from sqlmodel import BigInteger, Field, SQLModel, Relationship, Text
from sqlalchemy import Column, Enum, UniqueConstraint
from tidb_vector.sqlalchemy import VectorType

EMBED_DIM = 768

class PRState(enum.Enum):
    OPEN = "open" or "reopened"
    CLOSED = "closed"
    MERGED = "merged"

class IssueState(enum.Enum):
    OPEN = "open"
    CLOSED = "closed"


class Repository(SQLModel, table=True):
    id : int | None = Field(default=None, primary_key=True)
    owner : str
    gh_id : int = Field(index=True)

    commits : list["Commit"] = Relationship(back_populates="repo")
    prs : list["PullRequest"] = Relationship(back_populates="repo")
    issues : list["Issue"] = Relationship(back_populates="repo")

    __table_args__ = (
        UniqueConstraint("gh_id", name="uq_repo_gh_id"),
    )

class CommitPullRequestLink(SQLModel, table=True):
    commit_id: int = Field(foreign_key="git_commit.id", primary_key=True)
    pr_id: int = Field(foreign_key="pullrequest.id", primary_key=True)

class PullRequest(SQLModel, table=True):
    id : int | None = Field(default=None, primary_key=True)
    repo_id : int = Field(foreign_key="repository.id", index=True)
    number : int = Field(index=True)
    state : PRState = Field(sa_column=Column(Enum(PRState, name="pr_state")), default=PRState.OPEN)
    head_branch: str    # source
    base_branch: str    # target
 
    text: str
    embedding: list[float] = Field(
        sa_column=Column(VectorType(EMBED_DIM), nullable=False),
    )

    commits : list["Commit"] = Relationship(back_populates="prs", link_model=CommitPullRequestLink)
    repo : Repository = Relationship(back_populates="prs")
    issues : list["Issue"] = Relationship(back_populates="pr")
    reviews : list["Review"] = Relationship(back_populates="pr")

    __table_args__ = (
        UniqueConstraint("repo_id", "number", name="uq_pr_repo_number"),
    )

class Commit(SQLModel, table=True):
    id : int | None = Field(default=None, primary_key=True)
    repo_id : int = Field(foreign_key="repository.id", index=True)
    sha : str = Field(index=True)
    message : str = Field(sa_column=Column(Text))
    author_login : str | None = Field(default=None, index=True)
    created_at : datetime

    diff_text_embedding : list[float] = Field(
        sa_column=Column(VectorType(EMBED_DIM), nullable=False)
    )

    repo : Repository = Relationship(back_populates="commits")
    prs : list[PullRequest] = Relationship(back_populates="commits", link_model=CommitPullRequestLink)
    
    __tablename__ = "git_commit" # type: ignore
    __table_args__ = (
        UniqueConstraint("repo_id", "sha", name="uq_commit_repo_sha"),
    )

class Review(SQLModel, table=True):
    id : int | None = Field(default=None, primary_key=True)
    review_id : int = Field(sa_column=Column(BigInteger, index=True))
    comment_id : int | None = Field(sa_column=Column(BigInteger, index=True))
    pr_id : int = Field(foreign_key="pullrequest.id", index=True)
    comment_text : str | None
    
    review_type: str | None = Field(default=None, index=True) # "APPROVED", "CHANGES_REQUESTED", "COMMENTED", "INLINE"
    file_path: str | None
    line_number: int | None

    author_login : str | None
    created_at : datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    pr: PullRequest = Relationship(back_populates="reviews")

    __table_args__ = (
        UniqueConstraint("pr_id", "comment_id", name="uq_review_pr_commentid"),
        UniqueConstraint("pr_id", "review_id", name="uq_review_pr_reviewid"),
    )

class Issue(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    repo_id: int = Field(foreign_key="repository.id", index=True)
    number: int = Field(index=True)
    state: IssueState = Field(sa_column=Column(Enum(IssueState, name="issue_state")), default=IssueState.OPEN)
    content_embedding: list[float] = Field(
        sa_column=Column(VectorType(EMBED_DIM), nullable=False)
    )

    # optional association if a PR closes this issue
    pr_id: int | None = Field(default=None, foreign_key="pullrequest.id", index=True)

    repo: "Repository" = Relationship(back_populates="issues")
    pr: "PullRequest" = Relationship(back_populates="issues")
    files: list["IssueFile"] = Relationship(back_populates="issue")

    __table_args__ = (
        UniqueConstraint("repo_id", "number", name="uq_issue_repo_number"),
    )

class IssueFile(SQLModel, table=True):
    issue_id: int = Field(foreign_key="issue.id", primary_key=True)
    file_path: str = Field(primary_key=True, index=True)
    touches: int = Field(default=1)

    issue : Issue = Relationship(back_populates="files")