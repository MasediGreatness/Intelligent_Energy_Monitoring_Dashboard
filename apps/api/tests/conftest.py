import os

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://energy:@127.0.0.1:5432/energy_test"
)
os.environ.setdefault("APP_SECRET_KEY", "test-only-app-secret-key-32-characters")
os.environ.setdefault("INGEST_API_KEY", "test-only-ingest-api-key-value")
