"""
LexIntellectus ERP - Global Exception Handlers
Provides consistent error responses across the entire API.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, OperationalError
import traceback


def register_exception_handlers(app: FastAPI):
    """Register all global exception handlers on the FastAPI app."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Standard HTTP exceptions with consistent format."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.status_code,
                    "message": exc.detail,
                    "type": "http_error",
                },
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Pydantic validation errors — return detailed field errors."""
        errors = []
        for error in exc.errors():
            field = " → ".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field,
                "message": error["msg"],
                "type": error["type"],
            })

        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {
                    "code": 422,
                    "message": "Error de validación en los datos enviados",
                    "type": "validation_error",
                    "details": errors,
                },
            },
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        """Database integrity constraint violations (duplicate keys, FK errors)."""
        detail = str(exc.orig) if exc.orig else str(exc)

        # Detect common cases
        message = "Error de integridad en la base de datos"
        if "unique" in detail.lower() or "duplicate" in detail.lower():
            message = "Ya existe un registro con esos datos. Verifique campos únicos como email."
        elif "foreign key" in detail.lower():
            message = "Referencia inválida a un registro que no existe."

        return JSONResponse(
            status_code=409,
            content={
                "success": False,
                "error": {
                    "code": 409,
                    "message": message,
                    "type": "integrity_error",
                },
            },
        )

    @app.exception_handler(OperationalError)
    async def operational_error_handler(request: Request, exc: OperationalError):
        """Database connection/operational errors."""
        print(f"DB Operational Error: {exc}")
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": {
                    "code": 503,
                    "message": "Error de conexión con la base de datos. Intente nuevamente.",
                    "type": "database_error",
                },
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Catch-all for unhandled exceptions."""
        print(f"Unhandled exception: {type(exc).__name__}: {exc}")
        traceback.print_exc()

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": 500,
                    "message": "Error interno del servidor. El equipo técnico ha sido notificado.",
                    "type": "internal_error",
                },
            },
        )


# === File Upload Validation ===

ALLOWED_DOCUMENT_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".txt", ".rtf",
    ".xls", ".xlsx", ".csv",
    ".jpg", ".jpeg", ".png", ".gif", ".webp",
    ".odt", ".ods",
}

ALLOWED_DOCUMENT_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/rtf",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv",
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "application/vnd.oasis.opendocument.text",
    "application/vnd.oasis.opendocument.spreadsheet",
}

MAX_FILE_SIZE_MB = 25
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def validate_upload_file(filename: str, content_type: str, content_length: int):
    """
    Validate an uploaded file. Raises HTTPException if invalid.
    
    Args:
        filename: Original filename
        content_type: MIME type
        content_length: File size in bytes
    """
    import os

    # Check extension
    _, ext = os.path.splitext(filename.lower())
    if ext not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no permitido: '{ext}'. "
                   f"Extensiones válidas: {', '.join(sorted(ALLOWED_DOCUMENT_EXTENSIONS))}"
        )

    # Check MIME type
    if content_type and content_type not in ALLOWED_DOCUMENT_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo MIME no permitido: '{content_type}'."
        )

    # Check file size
    if content_length > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"El archivo excede el tamaño máximo de {MAX_FILE_SIZE_MB}MB. "
                   f"Tamaño recibido: {content_length / (1024*1024):.1f}MB."
        )
