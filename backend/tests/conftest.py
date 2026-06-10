import os

os.environ["TESTCONTAINERS_RYUK_DISABLED"] = "true"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

import app.models
from app.db.database import get_db
from app.main import app
from app.models.base import Base
from app.models.user import User as UserModel

os.environ["TESTCONTAINERS_RYUK_DISABLED"] = "true"


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:15-alpine") as postgres:
        yield postgres.get_connection_url()


@pytest.fixture(scope="session")
def test_engine(postgres_container):
    engine = create_engine(postgres_container)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_engine):
    connection = test_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def db(db_session):
    return db_session


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def register_and_verify(client, db_session):
    """Register a user and mark their email as verified so they can log in."""
    def _helper(payload: dict) -> dict:
        resp = client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 201
        user = db_session.query(UserModel).filter(UserModel.email == payload["email"]).first()
        user.is_email_verified = True
        db_session.commit()
        return resp.json()
    return _helper

@pytest.fixture
def auth_headers_profesional(client, register_and_verify):
    payload = {
        "email": "pro@test.com",
        "password": "strongpassword123",
        "full_name": "Test Pro",
        "role": "profesional",
        "phone": "+54 11 1234 5678",
        "specialty": "Dermatology"
    }
    register_and_verify(payload)
    resp = client.post("/api/v1/auth/login", json={"email": payload["email"], "password": payload["password"]})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def auth_headers_profesional_2(client, register_and_verify):
    payload = {
        "email": "pro2@test.com",
        "password": "strongpassword123",
        "full_name": "Test Pro 2",
        "role": "profesional",
        "phone": "+54 11 1234 5679",
        "specialty": "Pediatrics"
    }
    register_and_verify(payload)
    resp = client.post("/api/v1/auth/login", json={"email": payload["email"], "password": payload["password"]})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
