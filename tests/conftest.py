import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from postman_lab.main import Base, app, get_db, _fake_tasks_db


test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def reset_test_state():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    _fake_tasks_db.clear()

    yield

    _fake_tasks_db.clear()


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user():
    return {
        "email": "testuser@example.com",
        "password": "correctpassword123",
    }


@pytest.fixture
def registered_user(client, test_user):
    response = client.post(
        "/auth/register",
        json=test_user,
    )

    assert response.status_code == 201

    return test_user


@pytest.fixture
def auth_headers(client, registered_user):
    response = client.post(
        "/auth/login",
        json=registered_user,
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }