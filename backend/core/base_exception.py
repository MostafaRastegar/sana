import logging
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
    PermissionDenied,
)
from django.db.models import ProtectedError
from django.utils.translation import gettext_lazy as _
from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from http import HTTPStatus

logger = logging.getLogger(__name__)


class DmvnException(Exception):
    """
    Custom exception for DMVN project.

    Usage:
        raise DmvnException("Error message")  # Default 400 status
        raise DmvnException("permission_denied", status_code=403)
        raise DmvnException("validation_error", status_code=400, code="bad_request")
    """

    def __init__(self, message, status_code=400, code="invalid", details=None):
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or []
        super().__init__(message)


def create_error_response(status_code, message, details, code="invalid"):
    error_payload = {
        "error": {
            "status_code": status_code,
            "code": code,
            "message": message,
            "details": details or [],
        }
    }
    return error_payload


def custom_exception_handler(exc, context):
    view = context.get("view")
    module = getattr(view, "module_name", "core") if view else "core"

    if isinstance(exc, ProtectedError):
        return Response(
            create_error_response(
                status_code=400,
                message=_("can`t delete because of dependency."),
                details=[str(exc)],
                code="protected",
            ),
            status=400,
        )

    if isinstance(exc, DmvnException):
        message = exc.message
        if isinstance(message, str):
            message = _(message)
        return Response(
            create_error_response(
                status_code=exc.status_code,
                message=message,
                details=exc.details,
                code=exc.code,
            ),
            status=exc.status_code,
        )

    if isinstance(exc, DjangoValidationError):
        logger.warning(f"DjangoValidationError in {module}: {exc}")
        details = {}
        if hasattr(exc, "message_dict"):
            for field, msgs in exc.message_dict.items():
                details[field] = [str(m) for m in msgs]
        else:
            details = {"non_field_errors": [str(m) for m in exc.messages]}
        return Response(
            create_error_response(
                status_code=400,
                message=_("validation error."),
                details=details,
                code="bad_request",
            ),
            status=400,
        )

    if isinstance(exc, ValidationError):

        def flatten_error_detail(detail):
            if isinstance(detail, list):
                return {
                    "non_field_errors": [
                        str(item) if not hasattr(item, "message") else item.message
                        for item in detail
                    ]
                }
            elif isinstance(detail, dict):
                flattened = {}
                for key, value in detail.items():
                    if isinstance(value, (list, tuple)):
                        flattened[key] = [
                            str(v) if not hasattr(v, "message") else v.message
                            for v in value
                        ]
                    else:
                        flattened[key] = [
                            (
                                str(value)
                                if not hasattr(value, "message")
                                else value.message
                            )
                        ]
                return flattened
            else:
                return {
                    "non_field_errors": [
                        (
                            str(detail)
                            if not hasattr(detail, "message")
                            else detail.message
                        )
                    ]
                }

        details = flatten_error_detail(exc.detail)

        return Response(
            create_error_response(
                status_code=400,
                message=_("validation error."),
                details=details,
                code="bad_request",
            ),
            status=400,
        )

    if isinstance(exc, PermissionDenied):
        return Response(
            create_error_response(
                status_code=403,
                message=_("Dosen`t gave required permissions."),
                details=[str(exc)],
                code="forbidden",
            ),
            status=403,
        )

    response = exception_handler(exc, context)
    if response is not None:
        http_code_to_message = {v.value: v.description for v in HTTPStatus}
        status_code = response.status_code
        response.data = create_error_response(
            status_code=status_code,
            message=_(http_code_to_message.get(status_code, _("Unknown error."))),
            details=response.data,
        )
        return response

    logger.exception(exc)
    return Response(
        create_error_response(
            status_code=500,
            message=_("Unexpeceted server error."),
            details=[str(exc)],
            code="internal",
        ),
        status=500,
    )
