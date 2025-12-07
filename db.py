import os
import dotenv
from datetime import datetime, timezone
from sqlmodel import create_engine, SQLModel, Session, select
from sqlalchemy.engine import URL
from models import (
    PRState,
    IssueState,
    Repository,
    CommitPullRequestLink,
    PullRequest,
    Commit,
    Review,
    Issue,
    IssueFile
)
# from pytidb import TiDBClient

dotenv.load_dotenv()

db_host = os.getenv("DB_HOST")
db_username = os.getenv("DB_USERNAME")
db_password = os.getenv("DB_PASSWORD")
db_database = os.getenv("DB_DATABASE")
db_port = os.getenv("DB_PORT")
if not db_port is None:
    db_port = int(db_port)

ca_path = os.path.abspath("isrgrootx1.pem")

# tidb_client = TiDBClient.connect(
#     host=db_host,
#     port=db_port,
#     username=db_username,
#     password=db_password,
#     database=db_database,
#     ensure_db=True,
# )

def get_db_engine():
    connect_args = {}
    if ca_path:
        connect_args = {
            "ssl_verify_cert": True,
            "ssl_verify_identity": True,
            "ssl_ca": ca_path,
        }
    return create_engine(
        URL.create(
            drivername="mysql+pymysql",
            username=db_username,
            password=db_password,
            host=db_host,
            port=db_port, # type: ignore
            database=db_database,
        ),
        connect_args=connect_args,
        pool_pre_ping=True,
        future=True
    )

engine = get_db_engine()

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_db_url():
    url = URL.create(
        drivername="mysql+pymysql",
        username=db_username,
        password=db_password,
        host=db_host,
        port=db_port, # type: ignore
        database=db_database,
    )
    return url

def get_session():
    with Session(engine) as session:
        yield session

def upsert_repo(session: Session, gh_id: int, owner: str) -> Repository:
    repo = session.exec(select(Repository).where(Repository.gh_id == gh_id)).one_or_none()
    if repo:
        repo.owner = owner
    else:
        repo =  Repository(owner=owner,gh_id=gh_id)

    session.add(repo)
    session.flush()
    session.refresh(repo)
    return repo

def upsert_pr(session: Session, repo: Repository, number: int, state: PRState, text: str, embedding: list[float], head_branch: str, base_branch: str) -> PullRequest:
    pr = session.exec(select(PullRequest).where(PullRequest.repo_id == repo.id, PullRequest.number == number)).one_or_none()
    if pr:
        pr.state = state
        pr.text = text
        pr.embedding = embedding
        pr.head_branch = head_branch
        pr.base_branch = base_branch

    else:
        pr = PullRequest(repo_id=repo.id, number=number, state=state, text=text, embedding=embedding, head_branch=head_branch, base_branch=base_branch)

    session.add(pr)
    session.flush()
    session.refresh(pr)
    return pr

def upsert_review(session: Session, pr: PullRequest, review_id: int, comment_text: str, review_type: str, created_at: datetime, file_path: str | None = None, line_number: int | None = None, comment_id: int | None = None, author_login: str | None = None) -> Review:
    review = session.exec(select(Review).where(Review.pr_id == pr.id, Review.comment_id == comment_id, Review.review_id == review_id)).one_or_none()

    if review:
        review.comment_text = comment_text
        review.author_login = author_login
        review.review_type = review_type
        review.file_path = file_path
        review.line_number = line_number
        review.created_at = created_at
    else:
        review = Review(
            pr_id=pr.id,
            review_id=review_id,
            comment_id=comment_id,
            comment_text=comment_text,
            review_type=review_type,
            file_path=file_path,
            line_number=line_number,
            created_at=created_at,
            author_login=author_login,
        )
    session.add(review)
    session.flush()
    session.refresh(review)
    return review

def upsert_commit(
    session: Session,
    repo: Repository,
    sha: str,
    message: str,
    author_login: str | None,
    diff_embedding: list[float],
) -> Commit:
    c = session.exec(
    select(Commit).where(Commit.repo_id == repo.id, Commit.sha == sha)
    ).one_or_none()
    if c:
        c.message = message
        c.author_login = author_login
        c.diff_text_embedding = diff_embedding
    else:
        c = Commit(
            repo_id=repo.id,
            sha=sha,
            message=message,
            author_login=author_login,
            created_at=datetime.now(timezone.utc),
            diff_text_embedding=diff_embedding,
        )
    session.add(c)
    session.flush()
    session.refresh(c)
    return c

def link_commit_to_pr(session: Session, commit: Commit, pr: PullRequest) -> None:
    session.flush()
    link = session.get(CommitPullRequestLink, (commit.id, pr.id))
    if not link:
        session.add(CommitPullRequestLink(commit_id=commit.id, pr_id=pr.id))
        session.flush()

def get_issue(session: Session, repo: Repository, number: int) -> Issue | None:
    issue = session.exec(select(Issue).where(Issue.repo_id == repo.id, Issue.number == number)).one_or_none()
    return issue

def upsert_issue(session: Session, repo: Repository, number: int, state: IssueState, content_embedding: list[float], pr: PullRequest | None = None) -> Issue:
    issue = session.exec(select(Issue).where(Issue.repo_id == repo.id, Issue.number == number)).one_or_none()
    if issue:
        issue.state = state
        issue.content_embedding = content_embedding
    else:
        issue = Issue(
            repo_id=repo.id,
            number=number,
            state=state,
            content_embedding=content_embedding
        )
    session.add(issue)
    session.flush()
    session.refresh(issue)
    return issue

def link_issue_file(session: Session, issue: Issue, file_path: str, increment: int = 1) -> IssueFile:
    link = session.get(IssueFile, (issue.id, file_path))
    if link:
        link.touches = (link.touches or 0) + increment
    else:
        link = IssueFile(issue_id=issue.id, file_path=file_path, touches=increment)
    session.add(link)
    session.flush()
    session.refresh(link)
    return link
