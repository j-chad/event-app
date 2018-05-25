# coding=utf-8
from typing import Union

import wtforms
from flask_wtf import FlaskForm, RecaptchaField
from wtforms import ValidationError

from .extensions import bcrypt
from .models import User


class LoginForm(FlaskForm):
    email = wtforms.StringField(validators=[
        wtforms.validators.DataRequired(),
        wtforms.validators.Email(),
        wtforms.validators.Length(max=100)
    ])
    password = wtforms.PasswordField(validators=[
        wtforms.validators.DataRequired()
    ])

    def __init__(self, *args, **kwargs):
        # noinspection PyCallByClass
        FlaskForm.__init__(self, *args, **kwargs)
        self.user: Union[User, None] = None

    def validate(self) -> bool:
        rv = FlaskForm.validate(self)
        if not rv:
            return False
        user = User.query.filter_by(email=self.email.data).first()
        if user is None:
            # Hash random password anyways in an attempt to prevent timing attack
            bcrypt.generate_password_hash('lol random password' + 'random salt')
            self.password.errors.append("Unknown Username Or Password")
            return False
        else:
            if user.check_password(self.password.data):
                self.user = user
                return True
            else:
                self.password.errors.append("Unknown Username Or Password")
                return False


class RegisterForm(FlaskForm):
    first_name = wtforms.StringField(validators=[
        wtforms.validators.DataRequired(),
        wtforms.validators.Length(max=40)
    ])
    last_name = wtforms.StringField(validators=[
        wtforms.validators.Optional(),
        wtforms.validators.Length(max=40)
    ])
    email = wtforms.StringField(validators=[
        wtforms.validators.DataRequired(),
        wtforms.validators.Email(),
        wtforms.validators.Length(max=254)
    ])
    password = wtforms.PasswordField(validators=[
        wtforms.validators.DataRequired()
    ])
    recaptcha = RecaptchaField()


class RecoveryForm(FlaskForm):
    email = wtforms.StringField(validators=[
        wtforms.validators.DataRequired(),
        wtforms.validators.Email(),
        wtforms.validators.length(max=254)
    ])
    recaptcha = RecaptchaField()

    def __init__(self, *args, **kwargs):
        # noinspection PyCallByClass
        FlaskForm.__init__(self, *args, **kwargs)
        self.user: Union[User, None] = None

    def validate_email(self, field):
        self.user = User.query.get(field.data)
        if self.user is None:
            raise ValidationError("No Such User Exists")


class RecoveryPhase2Form(FlaskForm):
    email = wtforms.StringField(validators=[
        wtforms.validators.DataRequired(),
        wtforms.validators.Email(),
        wtforms.validators.length(max=254)
    ])
    first_name = wtforms.StringField(validators=[
        wtforms.validators.DataRequired(),
        wtforms.validators.length(max=40)
    ])
    password = wtforms.PasswordField(validators=[
        wtforms.validators.DataRequired(),
        wtforms.validators.EqualTo('confirm_password', message="Passwords Must Match")
    ])
    confirm_password = wtforms.PasswordField(validators=[
        wtforms.validators.DataRequired()
    ])
    recaptcha = RecaptchaField()


class CreateEventForm(FlaskForm):
    name = wtforms.StringField(validators=[
        wtforms.validators.DataRequired(),
        wtforms.validators.Length(max=60)
    ])
    description = wtforms.TextAreaField(validators=[
        wtforms.validators.Optional(),
        wtforms.validators.Length(max=200)
    ])
    private = wtforms.BooleanField(validators=[
        wtforms.validators.DataRequired()
    ])
