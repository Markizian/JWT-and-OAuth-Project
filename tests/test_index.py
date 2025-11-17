import pytest
from app.extensions import db
from run import create_app
from app.models import User

@pytest.fixture
def app():
    app = create_app("config.TestConfig") 
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()


def test_index_without_token(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Sign in" in response.data


def test_index_with_token(client, app, monkeypatch):
    def fake_authorize_access_token():
        return {"access_token": "fake"}
    def fake_get_userinfo():
        class FakeResp:
            def json(self):
                return {"email": "main@example.com", "name": "Main User"}
        return FakeResp()
    monkeypatch.setattr("app.extensions.oauth.google.authorize_access_token", fake_authorize_access_token)
    monkeypatch.setattr("app.extensions.oauth.google.get", lambda _: fake_get_userinfo())

    client.get("/auth/authorize")
    
    response = client.get("/")
    assert response.status_code == 200
    assert b"Main User" in response.data
