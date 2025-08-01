from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate

from .models import db
from .routes import tasks_bp
from .config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    Migrate(app, db)
    CSRFProtect(app)
    app.register_blueprint(tasks_bp)
    return app