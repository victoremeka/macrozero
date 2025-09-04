from sqlmodel import Field, SQLModel, Relationship, UniqueConstraint

class Review(SQLModel, table=True):
    repo_id: int = Field(primary_key=True, foreign_key="repository.id")
    commit_id: int = Field(primary_key=True, foreign_key="commit.id", ondelete="CASCADE")
    review: str

    commit: "Commit" = Relationship(back_populates="reviews")

class Commit(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    hash: str = Field(index=True) #TODO: Check with tidb if it supports creating multiple dbs from the api (manage scope globally or no)
    repo_id: int = Field(foreign_key="repository.id", ondelete="CASCADE")
    owner_id : int = Field(foreign_key="user.id")
    message: str

    reviews : list[Review] = Relationship(back_populates="commit", cascade_delete=True)
    repository : "Repository" = Relationship(back_populates="commits")
    user : "User" = Relationship(back_populates="commits")

    __table_args__ = (
        UniqueConstraint("repo_id", "hash"),
    )

class RepositoryLink(SQLModel, table=True):
    repo_id : int = Field(primary_key=True, foreign_key="repository.id")
    user_id : int = Field(primary_key=True, foreign_key="user.id")

class Repository(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str

    commits : list[Commit] = Relationship(back_populates="repository", cascade_delete=True)
    users : list["User"] = Relationship(back_populates="repositories", link_model=RepositoryLink)

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True)
    org: str | None = None

    commits : list[Commit] = Relationship(back_populates="user")
    repositories: list[Repository] = Relationship(back_populates="users", link_model=RepositoryLink)