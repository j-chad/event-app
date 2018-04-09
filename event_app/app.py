from typing import Any, Dict, Type

import flask

from .configs import Config, ProductionConfig
from .extensions import bcrypt, db, debug_toolbar, login_manager
from .models import User
from .views.home import home


def create_app(config_object: Type[Config] = ProductionConfig) -> flask.app.Flask:
    """Application Factory

    Creates and initialises the application"""

    app = flask.Flask(__name__.split('.')[0])  # Provide package name in case extensions make assumptions
    app.url_map.strict_slashes = False
    app.config.from_object(config_object)

    register_extensions(app)
    register_blueprints(app)
    register_shellcontext(app)

    return app


def register_extensions(app: flask.app.Flask) -> None:
    """Register All Flask Extensions"""
    bcrypt.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    debug_toolbar.init_app(app)

    # Set up user loader
    login_manager.user_loader(lambda user_id: User.query.get(int(user_id)))


def register_blueprints(app: flask.app.Flask) -> None:
    """Register Flask Blueprints"""
    app.register_blueprint(home)


def register_shellcontext(app: flask.app.Flask) -> None:
    """Register Flask Shell Context"""

    def shell_context() -> Dict[str, Any]:
        """Shell Context Objects"""
        return {
            'db': db
        }

    app.shell_context_processor(shell_context)
