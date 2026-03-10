import os
import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, get_db


load_dotenv()

# Use TEST_DATABASE_URL from environment
SQLALCHEMY_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL not set in environment")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


pytest_plugins = ["tests.fixtures"]


@pytest.fixture(scope="function")
def db():
    # using the test database
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Clean up after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
