from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from apscheduler.schedulers.background import BackgroundScheduler
from config import Config

# Extensions
mail = Mail()
db = SQLAlchemy()
login_manager = LoginManager()
scheduler = BackgroundScheduler()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    scheduler.start()

    from .routes.auth import auth_bp
    from .routes.dashboard import dashboard_bp
    from .routes.keywords import keywords_bp
    from .routes.admin import admin_bp
    from .routes.sync import sync_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(keywords_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(sync_bp)

    login_manager.login_view = 'auth.login'

    return app 