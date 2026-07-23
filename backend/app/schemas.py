from enum import StrEnum

from pydantic import BaseModel, Field


class Severity(StrEnum):
    """How much this comment should block a merge."""

    blocking = "Blocking"
    suggestion = "Suggestion"
    nitpick = "Nitpick"


class IssueCategory(StrEnum):
    """The five categories every review comment must be tagged with."""

    bug = "Bug"
    security = "Security"
    style_convention = "Style/Convention"
    performance = "Performance"
    best_practice = "Best Practice"


class Verdict(StrEnum):
    """The overall PR-style verdict, mirroring a real review's Approve/Request changes/Comment."""

    approve = "Approve"
    request_changes = "Request Changes"
    comment = "Comment"


class ReviewIssue(BaseModel):
    line: int | None = None
    severity: Severity
    category: IssueCategory
    message: str
    suggestion: str | None = None


class FileReview(BaseModel):
    path: str
    language: str | None = None
    verdict: Verdict
    justification: str
    summary: str
    issues: list[ReviewIssue] = Field(default_factory=list)


class ProjectReview(BaseModel):
    project_id: str
    files: list[FileReview]
    overall_verdict: Verdict
    overall_justification: str
    overall_summary: str


class UploadResponse(BaseModel):
    project_id: str
    file_count: int
    files: list[str]


class FileReviewRequest(BaseModel):
    project_id: str
    file_path: str


class SnippetReviewRequest(BaseModel):
    filename: str
    content: str


class DiffReviewRequest(BaseModel):
    """Stretch-goal input: a before/after pair, reviewed as a unified diff."""

    filename: str
    before: str
    after: str


class SourceType(StrEnum):
    """What kind of input POST /analyze was given."""

    github = "github"
    zip = "zip"
    file = "file"


class AnalyzeResponse(BaseModel):
    """Response for the single unified POST /analyze endpoint — handles all three
    input kinds (GitHub link, zip, single file) under one schema."""

    already_analyzed: bool
    source_type: SourceType
    identifier: str  # commit SHA (github) or sha256 content hash (zip/file)
    source_label: str  # repo URL, or the uploaded filename
    analyzed_at: str  # ISO-8601 timestamp
    project_id: str | None = None  # set for github/zip (multi-file); None for a single file
    project_review: ProjectReview | None = None
    file_review: FileReview | None = None


class HistoryEntry(BaseModel):
    source_type: SourceType
    identifier: str
    source_label: str
    analyzed_at: str


class AnalyzeRequest(BaseModel):
    """JSON-body variant of POST /analyze, for a GitHub link (no file upload)."""

    github_url: str
