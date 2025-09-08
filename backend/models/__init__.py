# Import models in proper order to avoid circular imports
from .enums import PRState, IssueState
from .repository import Repository
from .pull_request import PullRequest, CommitPullRequestLink, EMBED_DIM
from .commit import Commit
from .issue import Issue, IssueFile
from .review import Review

# Attempt to import VectorType for proper type checking
try:
    from tidb_vector.sqlalchemy import VectorType
except ImportError:
    # Fallback for VectorType if not available
    from sqlalchemy import ARRAY, Float

    class VectorType:
        def __init__(self, dim):
            self.dim = dim

        def __call__(self):
            return ARRAY(Float)


__all__ = [
    "PRState",
    "IssueState",
    "Repository",
    "PullRequest",
    "CommitPullRequestLink",
    "Commit",
    "Issue",
    "IssueFile",
    "Review",
    "EMBED_DIM",
]
