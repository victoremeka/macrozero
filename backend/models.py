from sqlmodel import Field, SQLModel, create_engine

class Review(SQLModel, table=True):
    repo_id: int = Field(primary_key=True, foreign_key="repository.id")
    commit_id: int = Field(primary_key=True, foreign_key="commit.id")
    review: str

class Commit(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    hash: str = Field(index=True, unique=True)
    message: str

class Repository(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    owner: int = Field(foreign_key="user.id")

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str
    org: str | None = None

