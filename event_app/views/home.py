# coding=utf-8

import flask
import flask_login

home = flask.Blueprint('home', __name__)


@home.route('/')
def index() -> flask.Response:
    if flask_login.current_user.is_authenticated:
        return flask.render_template("users/index_minimal.jinja")
    return flask.render_template("home/index_minimal.jinja")
