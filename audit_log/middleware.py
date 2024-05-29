import re

from audit_log.settings import audit_logging_settings
from audit_log.utils import commit_to_audit_log, get_response_status


class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if self._should_commit_to_audit_log(request, response):
            commit_to_audit_log(request, response)

        return response

    @staticmethod
    def _should_commit_to_audit_log(request, response):
        return (
            audit_logging_settings.ENABLED
            and re.match(audit_logging_settings.LOGGED_ENDPOINTS_RE, request.path)
            and get_response_status(response)
        )
