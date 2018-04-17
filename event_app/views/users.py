import flask
import flask_login
import flask_mail
from flask import Blueprint, render_template

from .. import forms, models, tasks, utils
from ..extensions import db

users = Blueprint('users', __name__)


@users.route('/login', methods=("GET", "POST"))
@utils.requires_anonymous()
def login():
    login_form = forms.LoginForm()
    if login_form.validate_on_submit():
        flask_login.login_user(login_form.user)
        flask.flash("Logged In Successfully", "success")
        return utils.redirect_with_next('home.index')
    return render_template('users/login_minimal.jinja', form=login_form)


@users.route('/register', methods=("GET", "POST"))
@utils.requires_anonymous()
def register():
    register_form = forms.RegisterForm()
    if register_form.validate_on_submit():
        user = models.User(first_name=register_form.first_name.data,
                           last_name=register_form.last_name.data,
                           email=register_form.email.data,
                           password=register_form.password.data)
        db.session.add(user)
        db.session.commit()
        flask_login.login_user(user)
        flask.flash("Please check your email", "info")
        return utils.redirect_with_next('home.index')
    return render_template('users/register_minimal.jinja', form=register_form)


@users.route('/logout')
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for("home.index"))


@users.route('/settings')
@flask_login.login_required
def settings():
    return "settings"
