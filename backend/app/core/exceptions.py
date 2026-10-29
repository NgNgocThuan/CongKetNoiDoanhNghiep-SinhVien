"""Exception nghiệp vụ + handler trả JSON thống nhất.

Service chỉ cần `raise NotFoundError("...")`, không tự tạo HTTPException.
Response lỗi luôn có dạng:  {"error": {"code": "NOT_FOUND", "message": "..."}}
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    status_code: int = 400
    code: str = "BAD_REQUEST"

    def __init__(self, message: str = "", *, code: str | None = None, status_code: int | None = None):
        super().__init__(message)
        self.message = message or self.__class__.__name__
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code


class BadRequestError(AppException):
    status_code, code = 400, "BAD_REQUEST"


class UnauthorizedError(AppException):
    status_code, code = 401, "UNAUTHORIZED"


class ForbiddenError(AppException):
    status_code, code = 403, "FORBIDDEN"


class NotFoundError(AppException):
    status_code, code = 404, "NOT_FOUND"


class ConflictError(AppException):
    status_code, code = 409, "CONFLICT"


class UnprocessableError(AppException):
    status_code, code = 422, "UNPROCESSABLE"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )
