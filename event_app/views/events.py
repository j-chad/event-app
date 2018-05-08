# coding=utf-8

import flask
from flask_login import login_required

users = flask.Blueprint('users', __name__)


@users.route('/event/create', methods=("GET", "POST"))
@login_required
def create_event() -> flask.Response:
    pass
