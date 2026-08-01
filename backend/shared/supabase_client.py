from supabase import create_client, Client

from config import settings

_supabase_client: Client | None = None


def get_supabase() -> Client:
    """Return a Supabase admin client using the service-role key."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_service_key,
        )
    return _supabase_client
