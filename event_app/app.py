# coding=utf-8
from typing import Any, Dict, Type

import flask
import flask_login

from . import commands, configs, extensions, forms, models, tasks, utils, views


def create_app(config_object: Type[configs.Config] = configs.ProductionConfig) -> flask.app.Flask:
    """Application Factory

    Creates and initialises the application"""

    app = flask.Flask(__name__.split('.')[0])  # Provide package name in case extensions make assumptions
    app.url_map.strict_slashes = False
    app.config.from_object(config_object)

    register_extensions(app)
    register_blueprints(app)
    register_commands(app)
    register_shellcontext(app)

    @app.context_processor
    def template_context():
        if flask_login.current_user is not None:  # Redis Queue Doesn't Seem To Play nice With This
            return {
                'user': flask_login.current_user,
                'channel': views.get_channel() if flask_login.current_user.is_authenticated else None
            }

    return app


def register_extensions(app: flask.app.Flask) -> None:
    """Register All Flask Extensions"""
    extensions.bcrypt.init_app(app)
    extensions.db.init_app(app)
    extensions.login_manager.init_app(app)
    extensions.mail.init_app(app)
    extensions.debug_toolbar.init_app(app)
    extensions.redis_queue.init_app(app)
    extensions.redis_store.init_app(app)
    extensions.limiter.init_app(app)
    extensions.humanise.init_app(app)

    # Set up user loader
    extensions.login_manager.user_loader(lambda token: models.User.query.filter_by(session_token=token).first())


def register_blueprints(app: flask.app.Flask) -> None:
    """Register Flask Blueprints"""
    app.register_blueprint(views.home)
    app.register_blueprint(views.users)
    app.register_blueprint(views.events)
    app.register_blueprint(views.ajax)
    app.register_blueprint(views.sse, url_prefix='/stream')


def register_commands(app: flask.app.Flask) -> None:
    app.cli.add_command(commands.build_database)
    app.cli.add_command(commands.populate_database)
    app.cli.add_command(commands.generate_markov)


def register_shellcontext(app: flask.app.Flask) -> None:
    """Register Flask Shell Context"""

    def shell_context() -> Dict[str, Any]:
        """Shell Context Objects"""
        return {
            'db': extensions.db,
            'models': models,
            'tasks': tasks,
            'mail': extensions.mail,
            'utils': utils,
            'forms': forms,
            'views': views
        }

    app.shell_context_processor(shell_context)
