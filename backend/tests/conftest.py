from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from cryptography.fernet import Fernet

from veya.domain.authentication.models import RefreshToken  # noqa: F401
from veya.domain.instagram.models import (  # noqa: F401
    InstagramAccount,
    InstagramComment,
    InstagramMedia,
)
from veya.domain.users.models import User  # noqa: F401
from veya.infrastructure.database.dependencies import get_db
from veya.infrastructure.database.session import Base
from veya.core.config import settings
from veya.main import app


TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def database() -> Generator[None, None, None]:
    settings.instagram_token_encryption_key = Fernet.generate_key().decode()
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
