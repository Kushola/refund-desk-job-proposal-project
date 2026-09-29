from flask import Flask
from flask_cors import CORS

from .config import Config
from .extensions import db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    CORS(app, origins=app.config["CORS_ORIGINS"])
    db.init_app(app)

    from .routes.customers import bp as customers_bp
    from .routes.refunds import bp as refunds_bp

    app.register_blueprint(customers_bp, url_prefix="/api")
    app.register_blueprint(refunds_bp, url_prefix="/api")

    @app.get("/api/health")
    def health():
        return {"status": "ok", "llm_enabled": bool(app.config["LLM_API_KEY"])}

    with app.app_context():
        from .models import Customer
        from .seed import seed_database

        db.create_all()
        if Customer.query.count() == 0:
            seed_database()

    return app
