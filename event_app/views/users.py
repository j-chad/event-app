import flask
from flask import Blueprint, render_template

from .. import forms, utils
from ..extensions import login_manager

users = Blueprint('users', __name__)


@users.route('/login', methods=("GET", "POST"))
def login():
    login_form = forms.LoginForm()
    if login_form.validate_on_submit():
        login_manager.login_user(login_form.user)
        flask.flash("Logged In Successfully", "success")
        return utils.redirect_with_next('home.index')
    return render_template('users/login_minimal.jinja', form=login_form)
