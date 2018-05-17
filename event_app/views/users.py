# coding=utf-8
from secrets import token_urlsafe
from typing import Union

import flask
import flask_login
import flask_mail
from flask import Blueprint, render_template
from flask_limiter.util import get_remote_address

from .. import forms, models, tasks, utils
from ..extensions import db, redis_store, limiter

users = Blueprint('users', __name__)


def send_validation_email(user: models.User, validation_token: str):
    email = "chadfield.jackson@gmail.com" if flask.helpers.get_debug_flag() else user.email
    msg = flask_mail.Message("This is my subject", recipients=[email])
    msg.html = flask.render_template('email/verification.jinja', user=user, token=validation_token)
    tasks.send_email.queue(msg)


def send_recovery_email(user: models.User, recovery_token: str):
    email = "chadfield.jackson@gmail.com" if flask.helpers.get_debug_flag() else user.email
    msg = flask_mail.Message("This is my subject", recipients=[email])
    msg.html = flask.render_template('email/recovery.jinja', user=user, token=recovery_token)
    tasks.send_email.queue(msg)


@users.route('/login', methods=("GET", "POST"))
@utils.requires_anonymous()
def login():
    login_form = forms.LoginForm()
    if flask.request.method == "POST":
        attempts: Union[bytes, None] = redis_store.get('USER:LOGIN_FAILURES#{}'.format(get_remote_address()))
        if attempts is not None and (int(attempts) >= flask.current_app.config["LOCKDOWN_AFTER_N_PASSWORD_ATTEMPTS"]):
            return render_template('users/login_minimal.jinja', form=login_form, lockout=True)
        elif login_form.validate():
            # Reset Attempt Count
            redis_store.delete('USER:LOGIN_FAILURES#{}'.format(get_remote_address()))
            flask_login.login_user(login_form.user)
            flask.flash("Logged In Successfully", "success")
            return utils.redirect_with_next('home.index')
        else:
            redis_store.incr('USER:LOGIN_FAILURES#{}'.format(get_remote_address()))
            # Reset Expiry Time
            redis_store.expire('USER:LOGIN_FAILURES#{}'.format(get_remote_address()),
                               flask.current_app.config["LOCKDOWN_FOR_N_SECONDS"])
        return render_template('users/login_minimal.jinja', form=login_form, lockout=False)


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
        token = str(token_urlsafe())
        redis_store.set('USER:VERIFICATION_TOKEN#{}'.format(token), user.email,
                        ex=flask.current_app.config['VERIFICATION_TOKEN_EXPIRY'],
                        nx=True)
        send_validation_email(user, token)
        flask.flash("Please check your email", "info")
        return utils.redirect_with_next('home.index')
    return render_template('users/register_minimal.jinja', form=register_form)


@users.route('/verify/<token>')
def activate_account(token):
    user_email: str = redis_store.get('USER:VERIFICATION_TOKEN#{}'.format(token))
    if user_email is None:
        flask.abort(404)
    else:
        user: models.User = models.User.query.get(user_email)
        if user is None or user.email_verified:
            flask.abort(404)
        else:
            redis_store.delete('USER:VERIFICATION_TOKEN#{}'.format(token))
            user.email_verified = True
            db.session.commit()
            flask.flash("Email Verified", "success")
            return flask.redirect(flask.url_for('home.index'))


@users.route('/verify/resend', methods=["GET"])  # TODO: Change To POST
@flask_login.login_required
@limiter.limit("1/hour", key_func=lambda: flask_login.current_user.email)
def resend_activation_email():
    user: models.User = flask_login.current_user
    token = str(token_urlsafe())
    redis_store.set('USER:VERIFICATION_TOKEN#{}'.format(token), user.email,
                    ex=flask.current_app.config['VERIFICATION_TOKEN_EXPIRY'],
                    nx=True)
    send_validation_email(user, token)
    return "OK"


@users.route('/recovery', methods=['GET', 'POST'])
@utils.requires_anonymous()
def recovery():  # TODO: Implement Lockout
    form = forms.RecoveryForm()
    if form.validate_on_submit():
        token = token_urlsafe()
        redis_store.set('USER:RECOVERY_TOKEN#{}'.format(token), form.user.email,
                        ex=flask.current_app.config['RECOVERY_TOKEN_EXPIRY'],
                        nx=True)
        send_recovery_email(form.user, token)
        flask.flash("Recovery Email Has Been Sent", "success")
        return flask.redirect(flask.url_for("home.index"))
    return flask.render_template("users/recovery_minimal.jinja", form=form)


@users.route('/recovery/<token>')
@utils.requires_anonymous()
def recovery_change_password(token):
    form = forms.RecoveryPhase2Form()
    user_email: str = redis_store.get('USER:RECOVERY_TOKEN#{}'.format(token))
    user: models.User = models.User.query.get(user_email)
    if user_email is None or user is None:
        flask.abort(404)
    else:
        if flask.request.method == "POST":
            if form.validate() \
                    and form.email.data == user_email \
                    and form.first_name.data.lower().strip() == user.first_name.lower().strip():
                redis_store.delete('USER:RECOVERY_TOKEN#{}'.format(token))
                user.password = form.password.data
                flask.flash("Password Has Been Reset", "success")
                flask_login.login_user(user)
                return flask.redirect(flask.url_for("home.index"))
            else:
                # TODO: Implement Lockout
                pass
        return flask.render_template('users/recovery_phase_2_minimal.jinja', form=form, token=token)



@users.route('/logout')
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for("home.index"))


@users.route('/settings')
@flask_login.login_required
def settings():
    return "settings"
