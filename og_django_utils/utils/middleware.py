import logging
import sys
import traceback

from django.core.exceptions import PermissionDenied
from django.http.response import Http404
from django.utils.deprecation import MiddlewareMixin
from django.utils.encoding import DjangoUnicodeDecodeError


class CriticalLogMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        # Skipped exceptions clogging the logfile
        if isinstance(exception, Http404) or isinstance(exception, PermissionDenied):
            return

        critical_logger = logging.getLogger("critical")
        critical_logger.critical("Critical error")
        critical_logger.critical(f"User: {request.user} [{request.user.id if request.user else None}]")
        critical_logger.critical("URL: %s", request.build_absolute_uri())

        ex_type, _ex, tb = sys.exc_info()
        critical_logger.critical(f"Exception type: {ex_type}")
        if isinstance(exception, DjangoUnicodeDecodeError):
            critical_logger.critical("Exception args:\n %s", repr(exception))
        else:
            critical_logger.critical("Exception message:\n %s", exception)
        critical_logger.critical("Exception traceback:\n %s", "".join(traceback.format_tb(tb, limit=20)))
