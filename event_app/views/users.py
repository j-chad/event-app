# coding=utf-8
from uuid import uuid4

import flask
import flask_login
import flask_mail
from flask import Blueprint, render_template

from .. import forms, models, tasks, utils
from ..extensions import db, redis_store, limiter

users = Blueprint('users', __name__)


def send_validation_email(user: models.User, token: str):
    email = "chadfield.jackson@gmail.com" if flask.helpers.get_debug_flag() else user.email
    msg = flask_mail.Message("This is my subject", recipients=[email])
    msg.html = flask.render_template('email/verification.jinja', user=user, token=token)
    tasks.send_email.queue(msg)


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
        token = str(uuid4())
        redis_store.set('USER:VERIFICATION_TOKEN#{}'.format(token), user.id,
                        ex=flask.current_app.config['VERIFICATION_TOKEN_EXPIRY'],
                        nx=True)
        send_validation_email(user, token)
        flask.flash("Please check your email", "info")
        return utils.redirect_with_next('home.index')
    return render_template('users/register_minimal.jinja', form=register_form)


@users.route('/verify/<uuid:token>')
def activate_account(token):
    user_id: int = int(redis_store.get('USER:VERIFICATION_TOKEN#{}'.format(token)))
    if user_id is None:
        flask.abort(404)
    else:
        user: models.User = models.User.query.get(user_id)
        if user is None:
            flask.abort(404)
        else:
            user.email_verified = True
            db.session.commit()
            flask.flash("Email Verified", "success")
            return flask.redirect(flask.url_for('home.index'))


@users.route('/verify/resend', methods=["GET"])  # TODO: Change To POST
@flask_login.login_required
@limiter.limit("1/hour", key_func=lambda: flask_login.current_user.email)
def resend_activation_email():
    user: models.User = flask_login.current_user
    token = str(uuid4())
    redis_store.set('USER:VERIFICATION_TOKEN#{}'.format(token), user.id,
                    ex=flask.current_app.config['VERIFICATION_TOKEN_EXPIRY'],
                    nx=True)
    send_validation_email(user, token)
    return "OK"


@users.route('/logout')
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for("home.index"))


@users.route('/settings')
@flask_login.login_required
def settings():
    return "settings"
