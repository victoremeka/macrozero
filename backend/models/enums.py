import enum


class PRState(enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


class IssueState(enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
