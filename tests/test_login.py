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


def test_login_sets_cookies(client, app, monkeypatch):
    def fake_authorize_access_token():
        return {"access_token": "fake"}

    def fake_get_userinfo():
        class FakeResp:
            def json(self):
                return {"email": "test@example.com", "name": "Test User"}
        return FakeResp()

    monkeypatch.setattr("app.extensions.oauth.google.authorize_access_token", fake_authorize_access_token)
    monkeypatch.setattr("app.extensions.oauth.google.get", lambda _: fake_get_userinfo())

    response = client.get("/auth/authorize", follow_redirects=True)

    assert response.status_code == 200
    cookies = response.headers.getlist("Set-Cookie")
    assert any("access_token_cookie" in c for c in cookies)
    assert any("refresh_token_cookie" in c for c in cookies)

    with app.app_context():
        user = User.query.filter_by(email="test@example.com").first()
        assert user is not None
