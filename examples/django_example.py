"""
Django integration example using _utils.

Demonstrates Django views and models with _utils integrations.
"""

from django.http import JsonResponse
from django.views import View

from _utils.exceptions import DatabaseError
from _utils.utils.logger import get_logger
from _utils.utils.sql import run_sql

# Initialize logger
logger = get_logger(__name__)


class DatabaseQueryView(View):
    """Django view for database queries using _utils."""

    def get(self, request) -> JsonResponse:
        """
        Handle GET request for database query.

        Args:
            request: Django request object

        Returns:
            JSON response with query results
        """
        query = request.GET.get("query", "SELECT 1")
        dbname = request.GET.get("dbname", "default")

        try:
            logger.info(
                "Executing database query",
                extra={
                    "dbname": dbname,
                    "user": request.user.username if hasattr(request, "user") else "anonymous",
                },
            )
            result = run_sql(query=query, queryType="query", dbname=dbname)
            return JsonResponse({"status": "success", "data": result})
        except DatabaseError as e:
            logger.exception("Database error", extra={"error": str(e)})
            return JsonResponse({"status": "error", "message": str(e)}, status=503)
        except Exception as e:
            logger.exception("Query failed", extra={"error": str(e)})
            return JsonResponse({"status": "error", "message": str(e)}, status=500)


# Django settings example
DJANGO_SETTINGS_EXAMPLE = """
# settings.py

# Configure logging using _utils
from _utils.utils.logger import configure_logging

configure_logging(level="INFO", use_json=False)

# Use _utils for database operations
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        # ... other settings
    }
}
"""
