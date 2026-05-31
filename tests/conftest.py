import os
import pytest

# Set test environment variables before any app imports
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/lungsight_test")
os.environ.setdefault("DATABASE_URL_SYNC", "postgresql://test:test@localhost:5432/lungsight_test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32chars-minimum!!")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-key-32chars-minimum!!!")
os.environ.setdefault("DEVICE", "cpu")
os.environ.setdefault("MODELS_DIR", "/tmp/lungsight_test_models")
os.environ.setdefault("UPLOAD_DIR", "/tmp/lungsight_test_uploads")
os.environ.setdefault("REPORTS_DIR", "/tmp/lungsight_test_reports")
