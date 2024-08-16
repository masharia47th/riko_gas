from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate  # Import Flask-Migrate

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'main.login'  # Ensure this matches your login route
migrate = Migrate()  # Initialize Migrate

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)  # Initialize Migrate with the app and db

    with app.app_context():
        from . import routes  # Import routes here
        from .models import User  # Import models here to avoid circular import

        # Register blueprints
        from .routes import main, admin
        app.register_blueprint(main)
        app.register_blueprint(admin)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))  # Load user by ID

    return app
