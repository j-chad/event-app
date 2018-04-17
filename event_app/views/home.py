import flask_login
from flask import Blueprint, render_template

home = Blueprint('home', __name__)


@home.route('/')
def index():
    if flask_login.current_user.is_authenticated:
        return render_template("users/index_minimal.jinja")
    return render_template("home/index_minimal.jinja")
