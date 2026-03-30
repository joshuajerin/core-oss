"""
GDPR data export service.

Collects all user data across tables and packages it as a JSON archive.
Returns a dict of table_name -> list[dict] suitable for ZIP packaging.
"""
import logging
from lib.supabase_client import get_service_role_client

logger = logging.getLogger(__name__)

# Tables to export and the column to filter by user ID
EXPORT_TABLES = [
    ("users", "id"),
    ("user_preferences", "user_id"),
    ("ext_connections", "user_id"),
    ("emails", "user_id"),
    ("calendar_events", "user_id"),
    ("documents", "created_by"),
    ("files", "uploaded_by"),
    ("conversations", "user_id"),
    ("notifications", "user_id"),
]

# Sensitive columns to redact from export
REDACT_COLUMNS = {"access_token", "refresh_token", "encrypted_access_token", "encrypted_refresh_token"}


def _redact_row(row: dict) -> dict:
    """Redact sensitive columns from a data row."""
    return {
        k: "***REDACTED***" if k in REDACT_COLUMNS else v
        for k, v in row.items()
    }


async def collect_user_data(user_id: str) -> dict[str, list[dict]]:
    """
    Collect all data associated with a user across all tables.

    Returns a dict mapping table names to lists of row dicts.
    Sensitive fields (tokens) are redacted.
    """
    supabase = get_service_role_client()
    export_data: dict[str, list[dict]] = {}

    for table_name, user_column in EXPORT_TABLES:
        try:
            result = supabase.table(table_name).select("*").eq(user_column, user_id).execute()
            rows = result.data or []
            export_data[table_name] = [_redact_row(row) for row in rows]
            logger.info(f"Exported {len(rows)} rows from {table_name} for user {user_id}")
        except Exception as e:
            logger.warning(f"Failed to export {table_name} for user {user_id}: {e}")
            export_data[table_name] = []

    # Also export workspace memberships
    try:
        result = supabase.table("workspace_members").select("*").eq("user_id", user_id).execute()
        export_data["workspace_memberships"] = result.data or []
    except Exception as e:
        logger.warning(f"Failed to export workspace_members for user {user_id}: {e}")
        export_data["workspace_memberships"] = []

    # Export channel memberships
    try:
        result = supabase.table("channel_members").select("*").eq("user_id", user_id).execute()
        export_data["channel_memberships"] = result.data or []
    except Exception as e:
        logger.warning(f"Failed to export channel_members for user {user_id}: {e}")
        export_data["channel_memberships"] = []

    return export_data
