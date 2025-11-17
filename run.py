from flask import Flask
from app.extensions import db, jwt
from app.oauth_providers import register_oauth_providers
from prometheus_flask_exporter import PrometheusMetrics
#import sentry_sdk
#from sentry_sdk.integrations.flask import FlaskIntegration
#from prometheus_flask_exporter import PrometheusMetrics

#sentry_sdk.init(
#    dsn="https://<PUBLIC_KEY>@sentry.io/<PROJECT_ID>",
#    integrations=[FlaskIntegration()],
#    traces_sample_rate=1.0
#)

def create_app(config_class="config.Config"):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    jwt.init_app(app)
    register_oauth_providers(app)

    from app.auth.routes import auth
    app.register_blueprint(auth, url_prefix="/auth")

    from app.main.routes import main
    app.register_blueprint(main, url_prefix="/")

    with app.app_context():
        db.create_all()

    return app

app = create_app()
metrics = PrometheusMetrics(app)

if __name__ == "__main__":
    app.run(debug=True)