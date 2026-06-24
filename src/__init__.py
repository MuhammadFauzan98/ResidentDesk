import os
from flask import Flask
from dotenv import load_dotenv

def createApp():
    app = Flask(__name__)

    load_dotenv()
    app.secret_key = os.getenv("SECRET_KEY", "society-management-app-secret-key-2026-development")

    from .routes import routes
    from .admin import admin
    from .flatOwner import flatOwner

    app.register_blueprint(routes, url_prefix="/")
    app.register_blueprint(admin, url_prefix="/")
    app.register_blueprint(flatOwner, url_prefix="/")

    return app