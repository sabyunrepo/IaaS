"""
backend/app/exceptions.py
애플리케이션 예외 계층
"""
from fastapi import HTTPException


class VantictBaseError(HTTPException):
    """기본 예외"""
    def __init__(self, status_code: int = 500, code: str = "INTERNAL_ERROR", message: str = "Internal server error"):
        self.code = code
        self.message = message
        super().__init__(status_code=status_code, detail={"code": code, "message": message})


class JobNotFoundError(VantictBaseError):
    def __init__(self, job_id: str):
        super().__init__(status_code=404, code="JOB_NOT_FOUND", message=f"Job not found: {job_id}")


class JobAlreadyExistsError(VantictBaseError):
    def __init__(self, job_id: str):
        super().__init__(status_code=409, code="JOB_EXISTS", message=f"Job already exists: {job_id}")


class AuthenticationError(VantictBaseError):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(status_code=401, code="UNAUTHORIZED", message=message)


class AuthorizationError(VantictBaseError):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(status_code=403, code="FORBIDDEN", message=message)


class ValidationError(VantictBaseError):
    def __init__(self, message: str):
        super().__init__(status_code=422, code="VALIDATION_ERROR", message=message)


class RateLimitError(VantictBaseError):
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(status_code=429, code="RATE_LIMITED", message=message)


class TemporalError(VantictBaseError):
    def __init__(self, message: str = "Workflow execution failed"):
        super().__init__(status_code=500, code="TEMPORAL_ERROR", message=message)


class DocumentParseError(VantictBaseError):
    def __init__(self, message: str, source: str = "unknown"):
        self.source = source
        super().__init__(status_code=422, code="DOCUMENT_PARSE_ERROR", message=message)


class LinkedInFetchError(VantictBaseError):
    def __init__(self, message: str = "LinkedIn profile fetch failed"):
        super().__init__(status_code=502, code="LINKEDIN_FETCH_ERROR", message=message)
