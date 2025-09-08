from datetime import datetime, timezone
from sqlmodel import Field, SQLModel
from sqlalchemy import UniqueConstraint


class Review(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    comment_id: str = Field(index=True)
    pr_id: int = Field(foreign_key="pullrequest.id", index=True)
    comment_text: str
    author_login: str | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("pr_id", "comment_id", name="uq_review_pr_comment"),
    )
