import wtforms
from flask_wtf import FlaskForm

from .extensions import bcrypt
from .models import User
from .utils import PasswordRules

# PASSWORD SETTINGS
p_manager = PasswordRules(
    uppercase=None,
    lowercase=None,
    digits=None,
    special=None,
    length=8
)


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
        self.user = None

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
        wtforms.validators.Length(max=100)
    ])
    password = wtforms.PasswordField(validators=[
        wtforms.validators.DataRequired(),
        p_manager
    ])
