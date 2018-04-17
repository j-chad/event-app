from typing import Any, Dict, Type

import flask

from . import commands, configs, extensions, models, tasks, views


def create_app(config_object: Type[configs.Config] = configs.ProductionConfig) -> flask.app.Flask:
    """Application Factory

    Creates and initialises the application"""

    app = flask.Flask(__name__.split('.')[0],
                      instance_relative_config=True)  # Provide package name in case extensions make assumptions
    app.url_map.strict_slashes = False
    app.config.from_object(config_object)
    app.config.from_pyfile("config.py")

    register_extensions(app)
    register_blueprints(app)
    register_commands(app)
    register_shellcontext(app)

    return app


def register_extensions(app: flask.app.Flask) -> None:
    """Register All Flask Extensions"""
    extensions.bcrypt.init_app(app)
    extensions.db.init_app(app)
    extensions.login_manager.init_app(app)
    extensions.mail.init_app(app)
    extensions.debug_toolbar.init_app(app)
    extensions.redis_queue.init_app(app)

    # Set up user loader
    extensions.login_manager.user_loader(lambda token: models.User.query.filter_by(session_token=token).first())


def register_blueprints(app: flask.app.Flask) -> None:
    """Register Flask Blueprints"""
    app.register_blueprint(views.home)
    app.register_blueprint(views.users)


def register_commands(app: flask.app.Flask) -> None:
    app.cli.add_command(commands.build_database)


def register_shellcontext(app: flask.app.Flask) -> None:
    """Register Flask Shell Context"""

    def shell_context() -> Dict[str, Any]:
        """Shell Context Objects"""
        return {
            'db'   : extensions.db,
            'User' : models.User,
            'Event': models.Event,
            'tasks': tasks
        }

    app.shell_context_processor(shell_context)
