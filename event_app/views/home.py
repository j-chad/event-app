# coding=utf-8

import flask
import flask_login

home = flask.Blueprint('home', __name__, static_folder="static")


@home.route('/')
def index() -> flask.Response:
    if flask_login.current_user.is_authenticated:
        return flask.render_template("users/index_minimal.jinja")
    return flask.render_template("home/index_minimal.jinja")


@home.route('/service-worker.js')
def serve_worker() -> flask.Response:
    return flask.send_file('static/service-worker.js', mimetype="application/javascript")
