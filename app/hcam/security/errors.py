from __future__ import annotations

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def _safe_validation_message(error_type: str) -> str:
    if error_type == "missing":
        return "Field required"
    if error_type == "extra_forbidden":
        return "Extra input is not permitted"
    return "Invalid request value"


async def sanitized_request_validation_error(
    _request: Request,
    error: RequestValidationError,
) -> JSONResponse:
    details: list[dict[str, object]] = []
    for item in error.errors():
        error_type = str(item.get("type") or "value_error")
        location = [
            value
            for value in item.get("loc", ())
            if isinstance(value, (str, int))
        ]
        details.append(
            {
                "type": error_type,
                "loc": location,
                "msg": _safe_validation_message(error_type),
            }
        )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": details},
        headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
    )
