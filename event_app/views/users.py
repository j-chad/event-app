import flask
import flask_login
from flask import Blueprint, render_template

from .. import forms, models, utils

users = Blueprint('users', __name__)


@users.route('/login', methods=("GET", "POST"))
def login():
    login_form = forms.LoginForm()
    if login_form.validate_on_submit():
        flask_login.login_user(login_form.user)
        flask.flash("Logged In Successfully", "success")
        return utils.redirect_with_next('home.index')
    return render_template('users/login_minimal.jinja', form=login_form)


@users.route('/register', methods=("GET", "POST"))
def register():
    register_form = forms.RegisterForm()
    if register_form.validate_on_submit():
        user = models.User(first_name=register_form.first_name.data,
                           last_name=register_form.last_name.data,
                           email=register_form.email.data,
                           password=register_form.password.data)
        user.save(commit=True)
        flask_login.login_user(user)
        flask.flash("Please check your email", "info")
        return utils.redirect_with_next('home.index')
    return render_template('users/register_minimal.jinja', form=register_form)
