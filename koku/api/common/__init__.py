# noqa
from django.db import connection
from django.utils.translation import ugettext as _

RH_IDENTITY_HEADER = "HTTP_X_RH_IDENTITY"

# Django will add the HTTP automatically when checking headers
CACHE_RH_IDENTITY_HEADER = "X_RH_IDENTITY"


def error_obj(key, message):
    """Create an error object."""
    error = {key: [_(message)]}
    return error


def log_json(tracing_id, message, context={}):
    """Create JSON object for logging data."""
    if connection.connection and not connection.connection.closed:
        message = f"DBPID_{connection.connection.get_backend_pid()} {message}"
    stmt = {"message": message, "tracing_id": tracing_id}
    stmt.update(context)
    return stmt
