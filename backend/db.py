import os
import dotenv
from sqlmodel import create_engine, Session, select
from sqlalchemy.engine import URL
from models import *

dotenv.load_dotenv()

db_host = os.getenv("DB_HOST")
db_username = os.getenv("DB_USERNAME")
db_password = os.getenv("DB_PASSWORD")
db_database = os.getenv("DB_DATABASE")
db_port = os.getenv("DB_PORT")
if not db_port is None:
    db_port = int(db_port)

ca_path = os.path.abspath("isrgrootx1.pem")

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
        echo=True # reminder: take out in prod
    )

engine = get_db_engine()

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def upsert_repo(gh_id: int, owner: str) -> Repository:
    with Session(engine) as session:
        repo = session.exec(select(Repository).where(Repository.gh_id == gh_id)).one_or_none()
        if repo:
            repo.owner = owner
        else:
            repo =  Repository(owner=owner,gh_id=gh_id)
        
        session.add(repo)
        session.commit()
        session.refresh(repo)
        return repo
    
def upsert_pr(repo: Repository, number: int, state: PRState, text: str, embedding: list[float]) -> PullRequest:
    with Session(engine) as session:
        pr = session.exec(select(PullRequest).where(PullRequest.repo_id == repo.id, PullRequest.number == number)).one_or_none()
        if pr:
            pr.state = state
            pr.text = text
            pr.embedding = embedding
        else:
            pr = PullRequest(repo_id=repo.id, number=number, state=state, text=text, embedding=embedding)
        
        session.add(pr)
        session.commit()
        session.refresh(pr)
        return pr

def upsert_commit(
    repo: Repository,
    sha: str,
    message: str,
    author_login: str | None,
    diff_text_raw: str,
    diff_embedding: list[float],
) -> Commit:
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
    with Session(engine) as session:
        session.flush()
        link = session.get(CommitPullRequestLink, (commit.id, pr.id))
        if not link:
            session.add(CommitPullRequestLink(commit_id=commit.id, pr_id=pr.id))
            session.commit()

def upsert_issue(repo: Repository, number: int, state: IssueState, pr: PullRequest | None = None) -> Issue:
    with Session(engine) as session:
        issue = session.exec(select(Issue).where(Issue.repo_id == repo.id, Issue.number == number)).one_or_none()
        if issue:
            issue.state = state
        else:
            issue = Issue(
                repo_id=repo.id,
                number=number,
                state=state,
            )
        session.add(issue)
        session.commit()
        session.refresh(issue)
        return issue
    
def link_issue_file(issue: Issue, file_path: str, increment: int = 1) -> IssueFile:
    with Session(engine) as session:
        link = session.get(IssueFile, (issue.id, file_path))
        if link:
            link.touches = (link.touches or 0) + increment
        else:
            link = IssueFile(issue_id=issue.id, file_path=file_path, touches=increment)
        session.add(link)
        session.commit()
        session.refresh(link)
        return link


    
if __name__ == "__main__":
    create_db_and_tables()