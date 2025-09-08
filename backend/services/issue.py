from sqlmodel import select, Session
from models import Issue, Repository, IssueState, PullRequest, IssueFile
from core.database import engine
from typing import Optional


def upsert_issue(
    repo: Repository, number: int, state: IssueState, pr: Optional[PullRequest] = None
) -> Issue:
    """
    Create or update an issue
    """
    with Session(engine) as session:
        issue = session.exec(
            select(Issue).where(Issue.repo_id == repo.id, Issue.number == number)
        ).one_or_none()

        if issue:
            issue.state = state
            if pr:
                issue.pr_id = pr.id
        else:
            issue = Issue(
                repo_id=repo.id, number=number, state=state, pr_id=pr.id if pr else None
            )

        session.add(issue)
        session.commit()
        session.refresh(issue)
        return issue


def link_issue_file(issue: Issue, file_path: str, increment: int = 1) -> IssueFile:
    """
    Link a file to an issue and update touch count
    """
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
