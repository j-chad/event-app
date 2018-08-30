# coding=utf-8

import flask
import flask_login
from werkzeug.utils import secure_filename

from ..forms import RegisterForm
from ..views.users import dashboard

home = flask.Blueprint('home', __name__, static_folder="static")


@home.route('/')
def index():
    if flask_login.current_user.is_authenticated:
        return dashboard()
    form = RegisterForm()
    return flask.render_template("home/index.jinja", form=form)


@home.route('/<path:filename>')  # Development Only, Use Nginx In Prod.
def custom_static(filename):
    filename = secure_filename(filename)
    return flask.send_from_directory("root_static", filename)
