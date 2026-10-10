import os

APP_ENV = os.getenv("APP_ENV", "development")
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_PUBLISHABLE_KEY = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

def supabase_client_key() -> str:
    return SUPABASE_PUBLISHABLE_KEY or SUPABASE_ANON_KEY

def cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    return [x.strip() for x in raw.split(",") if x.strip()]

PRECISION_URL = os.getenv("PRECISION_URL", "https://diag.lpp20.com/").strip()
