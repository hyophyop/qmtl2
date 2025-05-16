from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from qmtl.common.errors.exceptions import (
    AuthError,
    DatabaseError,
    HTTPError,
    NotFoundError,
    QMTLError,
    ValidationError,
)


def qmtl_exception_handler(request: Request, exc: QMTLError):
    if isinstance(exc, HTTPError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    if isinstance(exc, ValidationError):
        return JSONResponse(status_code=422, content={"detail": str(exc)})
    if isinstance(exc, NotFoundError):
        return JSONResponse(status_code=404, content={"detail": str(exc)})
    if isinstance(exc, AuthError):
        return JSONResponse(status_code=401, content={"detail": str(exc)})
    if isinstance(exc, DatabaseError):
        return JSONResponse(status_code=500, content={"detail": str(exc)})
    return JSONResponse(status_code=500, content={"detail": str(exc)})


def register_qmtl_exception_handlers(app):
    app.add_exception_handler(QMTLError, qmtl_exception_handler)
    app.add_exception_handler(
        HTTPException,
        lambda req, exc: JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}),
    )


# 기존 코드와의 호환성을 위한 별칭
add_exception_handlers = register_qmtl_exception_handlers
