"""FastAPI application factory and configuration."""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import (
    AIServiceError,
    AppError,
    AuthorizationError,
    ConflictError,
    EvaluationValidationError,
    MessageLimitError,
    MinimumMessagesError,
    ResourceNotFoundError,
    SessionStateError,
    ValidationError,
)
from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)

# Map each domain exception to an HTTP status code.
_EXCEPTION_STATUS: dict[type[AppError], int] = {
    ResourceNotFoundError: status.HTTP_404_NOT_FOUND,
    AuthorizationError: status.HTTP_403_FORBIDDEN,
    MinimumMessagesError: status.HTTP_400_BAD_REQUEST,
    ValidationError: status.HTTP_400_BAD_REQUEST,
    ConflictError: status.HTTP_409_CONFLICT,
    SessionStateError: status.HTTP_409_CONFLICT,
    MessageLimitError: status.HTTP_409_CONFLICT,
    AIServiceError: status.HTTP_502_BAD_GATEWAY,
    EvaluationValidationError: status.HTTP_502_BAD_GATEWAY,
}


def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        code = _EXCEPTION_STATUS.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
        if code >= 500:
            logger.error("Unhandled application error: %s", type(exc).__name__)
        return JSONResponse(status_code=code, content={"detail": exc.message})


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        debug=settings.debug,
    )

    # In development, also allow any localhost / 127.0.0.1 port so the Vite dev
    # server works regardless of which port it picks. Production relies on the
    # explicit CORS_ORIGINS allowlist.
    cors_kwargs: dict[str, object] = {
        "allow_origins": settings.cors_origins,
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }
    if settings.debug:
        cors_kwargs["allow_origin_regex"] = r"https?://(localhost|127\.0\.0\.1)(:\d+)?"

    app.add_middleware(CORSMiddleware, **cors_kwargs)

    _register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {"service": settings.app_name, "docs": "/docs"}

    return app


app = create_app()
