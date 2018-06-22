# coding=utf-8

import flask
import flask_login

from ..forms import RegisterForm
from ..views.users import dashboard

home = flask.Blueprint('home', __name__, static_folder="static")


@home.route('/')
def index() -> flask.Response:
    if flask_login.current_user.is_authenticated:
        return dashboard()
    form = RegisterForm()
    return flask.render_template("home/index.jinja", form=form)


@home.route('/service-worker.js')
def serve_worker() -> flask.Response:
    return flask.send_file('static/js/service-worker.js', mimetype="application/javascript")
