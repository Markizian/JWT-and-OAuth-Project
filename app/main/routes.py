from flask import render_template, Blueprint, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models import User, TokenBlocklist
from app.extensions import db

main = Blueprint("main", __name__)


# Routes
@main.route("/")
def index():
    verify_jwt_in_request(optional=True)
    user_id = get_jwt_identity()
    if user_id:
        user = db.session.get(User, user_id)
    else:
        user = None

    data = {
        "user": user,
        "access": request.cookies.get("access_token_cookie"),
        "refresh": request.cookies.get("refresh_token_cookie")
    }
    return render_template("index.html", data=data)


@main.route("/database")
def database():
    data = {
        "users": User.query.all(),
        "tokens": TokenBlocklist.query.all()
    }
    return render_template("database.html", data=data)