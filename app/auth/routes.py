from datetime import datetime
from flask import Blueprint, url_for, make_response, render_template
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt,
    set_access_cookies, set_refresh_cookies
)
from ..models import User, TokenBlocklist
from ..extensions import jwt, db
from app.extensions import oauth

auth = Blueprint("auth", __name__)


# Check blocklist
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    token = TokenBlocklist.query.filter_by(jti=jti).first()
    return token is not None

# Check token if revoked
@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    token_type = jwt_payload.get("type", "unknown")
    return render_template("index.html", data=None, message=f"{token_type} token revoked", token_type=token_type)

# Check token if expired
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    token_type = jwt_payload.get("type", "unknown")
    return render_template("index.html", data=None, message=f"{token_type} token expired", token_type=token_type)


@auth.route("/login")
def login():
    redirect_uri = url_for("auth.authorize", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth.route("/authorize")
def authorize():
    token = oauth.google.authorize_access_token()
    user_info = oauth.google.get("userinfo").json()
    email = user_info["email"]
    name = user_info["name"]

    user = User.query.filter_by(email=email).first()
    
    if not user:
        user = User(email=email, name=name)
        db.session.add(user)
        db.session.commit()

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    response = make_response(render_template('message.html', message="Login successful!"))
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)

    return response


@auth.route("/refresh")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    new_access = create_access_token(identity=identity)

    response = make_response(render_template('message.html', message="Access token refreshed!"))
    set_access_cookies(response, new_access)

    return response


@auth.route("/logout_access")
@jwt_required()
def logout_access():
    jti = get_jwt()["jti"]
    now = datetime.now()
    db.session.add(TokenBlocklist(jti=jti, token_type="access", created_at=now))
    db.session.commit()

    return render_template("message.html", message="Access token withdrawn")


@auth.route("/logout_refresh")
@jwt_required(refresh=True)
def logout_refresh():
    jti = get_jwt()["jti"]
    now = datetime.now()
    db.session.add(TokenBlocklist(jti=jti, token_type="refresh", created_at=now))
    db.session.commit()

    return render_template("message.html", message="Refresh token withdrawn")
