from flask import Blueprint
from flask_login import login_required

users = Blueprint('users', __name__)


@users.route('/event/create', methods=("GET", "POST"))
@login_required
def create_event():
    pass
