"""
GDPR account deletion service.

Implements soft-delete with a 30-day grace period. During the grace period,
the user can cancel deletion. After 30 days, a cron job triggers hard deletion
which cascades across all user data.
"""
import logging
from datetime import datetime, timezone
from lib.supabase_client import get_service_role_client

logger = logging.getLogger(__name__)


async def request_account_deletion(user_id: str) -> dict:
    """
    Mark a user account for deletion with a 30-day grace period.

    Sets `pending_deletion_at` to the current timestamp. The account
    will be hard-deleted by the cleanup cron after 30 days.
    """
    supabase = get_service_role_client()
    now = datetime.now(timezone.utc).isoformat()

    result = supabase.table("users").update({
        "pending_deletion_at": now,
    }).eq("id", user_id).execute()

    if not result.data:
        raise ValueError("User not found")

    logger.info(f"Account deletion requested for user {user_id} at {now}")
    return {"pending_deletion_at": now}


async def cancel_account_deletion(user_id: str) -> None:
    """
    Cancel a pending account deletion.

    Clears the `pending_deletion_at` field, stopping the 30-day countdown.
    """
    supabase = get_service_role_client()

    result = supabase.table("users").update({
        "pending_deletion_at": None,
    }).eq("id", user_id).execute()

    if not result.data:
        raise ValueError("User not found")

    logger.info(f"Account deletion cancelled for user {user_id}")


async def hard_delete_user(user_id: str) -> None:
    """
    Permanently delete all user data. Called by cron after the grace period.

    Deletion order matters due to foreign key constraints:
    1. Messages and reactions
    2. Channel memberships
    3. Documents and files metadata
    4. Email data
    5. Calendar data
    6. Conversations (AI chat)
    7. Notifications
    8. Workspace memberships (but NOT workspaces they own — those need separate handling)
    9. External connections (OAuth tokens)
    10. User preferences
    11. User record
    12. Supabase auth user (via admin API)
    """
    supabase = get_service_role_client()

    # Order of deletion (child tables first)
    tables_to_clear = [
        ("notifications", "user_id"),
        ("channel_members", "user_id"),
        ("conversations", "user_id"),
        ("calendar_events", "user_id"),
        ("emails", "user_id"),
        ("documents", "created_by"),
        ("files", "uploaded_by"),
        ("user_preferences", "user_id"),
        ("ext_connections", "user_id"),
        ("workspace_members", "user_id"),
    ]

    for table_name, user_column in tables_to_clear:
        try:
            supabase.table(table_name).delete().eq(user_column, user_id).execute()
            logger.info(f"Deleted {table_name} rows for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to delete {table_name} for user {user_id}: {e}")

    # Delete user record
    try:
        supabase.table("users").delete().eq("id", user_id).execute()
        logger.info(f"Deleted user record for {user_id}")
    except Exception as e:
        logger.error(f"Failed to delete user record for {user_id}: {e}")

    # Delete from Supabase Auth
    try:
        supabase.auth.admin.delete_user(user_id)
        logger.info(f"Deleted Supabase auth user {user_id}")
    except Exception as e:
        logger.error(f"Failed to delete Supabase auth user {user_id}: {e}")

    logger.info(f"Hard delete completed for user {user_id}")
