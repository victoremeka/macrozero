from integrations.github_client import *
from models import *
from db import (
    upsert_repo,
    upsert_pr,
    upsert_commit,
    upsert_issue,
    link_commit_to_pr,
    link_issue_file,
)

def handle_pull_request():
    pass

def handle_issue():
    pass