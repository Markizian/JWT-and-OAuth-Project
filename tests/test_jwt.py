import pytest
from app.extensions import db
from run import create_app
from app.models import TokenBlocklist

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


def test_refresh_token(client, app, monkeypatch):
    def fake_authorize_access_token():
        return {"access_token": "fake"}
    def fake_get_userinfo():
        class FakeResp:
            def json(self):
                return {"email": "refresh@example.com", "name": "Ref User"}
        return FakeResp()

    monkeypatch.setattr("app.extensions.oauth.google.authorize_access_token", fake_authorize_access_token)
    monkeypatch.setattr("app.extensions.oauth.google.get", lambda _: fake_get_userinfo())

    client.get("/auth/authorize")

    response = client.get("/auth/refresh")
    assert response.status_code == 200
    assert b"Access token refreshed!" in response.data
    cookies = response.headers.getlist("Set-Cookie")
    assert any("access_token_cookie" in c for c in cookies)


def test_logout_access_adds_blocklist(client, app, monkeypatch):
    def fake_authorize_access_token():
        return {"access_token": "fake"}
    def fake_get_userinfo():
        class FakeResp:
            def json(self):
                return {"email": "logout@example.com", "name": "Logout User"}
        return FakeResp()
    monkeypatch.setattr("app.extensions.oauth.google.authorize_access_token", fake_authorize_access_token)
    monkeypatch.setattr("app.extensions.oauth.google.get", lambda _: fake_get_userinfo())

    client.get("/auth/authorize")

    response = client.get("/auth/logout_access")
    assert b"Access token withdrawn" in response.data

    with app.app_context():
        tokens = TokenBlocklist.query.all()
        assert len(tokens) == 1
        assert tokens[0].token_type == "access"


def test_logout_access_revokes_token(client, app, monkeypatch):
    def fake_authorize_access_token():
        return {"access_token": "fake"}
    def fake_get_userinfo():
        class FakeResp:
            def json(self):
                return {"email": "logout@example.com", "name": "Logout User"}
        return FakeResp()
    monkeypatch.setattr("app.extensions.oauth.google.authorize_access_token", fake_authorize_access_token)
    monkeypatch.setattr("app.extensions.oauth.google.get", lambda _: fake_get_userinfo())

    client.get("/auth/authorize")

    response = client.get("/auth/logout_access")
    assert response.status_code == 200
    assert b"Access token withdrawn" in response.data

    with app.app_context():
        assert TokenBlocklist.query.count() == 1

    response2 = client.get("/")
    assert response2.status_code == 200
    assert b"access token revoked" in response2.data


def test_logout_refresh_revokes_token(client, app, monkeypatch):
    def fake_authorize_access_token():
        return {"access_token": "fake"}
    def fake_get_userinfo():
        class FakeResp:
            def json(self):
                return {"email": "logout@example.com", "name": "Logout User"}
        return FakeResp()
    monkeypatch.setattr("app.extensions.oauth.google.authorize_access_token", fake_authorize_access_token)
    monkeypatch.setattr("app.extensions.oauth.google.get", lambda _: fake_get_userinfo())

    client.get("/auth/authorize")

    response = client.get("/auth/logout_refresh")
    assert response.status_code == 200
    assert b"Refresh token withdrawn" in response.data

    with app.app_context():
        token = TokenBlocklist.query.filter_by(token_type="refresh").first()
        assert token is not None

    response2 = client.get("/auth/refresh")
    assert response2.status_code == 200
    assert b"refresh token revoked" in response2.data
