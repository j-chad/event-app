import random
import string
import uuid
from datetime import datetime

from flask_login import UserMixin
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property

from .extensions import bcrypt, db
from .util import reference_col

Model = db.Model
Column = db.Column
ForeignKey = db.ForeignKey
relationship = db.relationship


class Session(Model):
    __tablename__ = 'sessions'
    id = Column(db.String(32), primary_key=True, default=lambda: uuid.uuid4().hex)


class User(UserMixin, Model):
    __tablename__ = 'users'
    id = Column(db.Integer, primary_key=True)
    first_name = Column(db.String(40), nullable=False)
    last_name = Column(db.String(40), nullable=True)
    email = Column(db.String(100), unique=True, nullable=False)
    email_verified = Column(db.Boolean, nullable=False)
    _password = Column(db.Binary(128), nullable=False)
    created_at = Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # FLASK-LOGIN

    def __init__(self, first_name: str, email: str, password: str = None, **kwargs):
        super().__init__(self, first_name=first_name, email=email, **kwargs)
        if password is not None:
            self.password = password

    @hybrid_property
    def password(self) -> str:
        """This enables abstraction away from the _password"""
        return self._password

    @password.setter
    def password(self, plain_password: str) -> None:
        """Enables Super Simple And Safe Password Saving

        Instead of hashing the password manually each time it needs to be changed,
        this function allows us to simply specify `User.password = "newpassword"`.
        And the password will be converted and saved appropriately.
        """
        salted_password = plain_password + self.salt
        self._password = bcrypt.generate_password_hash(salted_password, rounds=db.app.config['BCRYPT_LOG_ROUNDS'])

    @hybrid_method
    def check_password(self, plain_password: str) -> bool:
        """Checks If The User Entered The Right Password"""
        salted_password = plain_password + self.salt
        return bcrypt.check_password_hash(self.password, salted_password)

    def __repr__(self):
        return "<User({!r})>".format(self.username)


class Event(Model):
    __tablename__ = 'events'
    id = Column(db.String(10), primary_key=True)
    name = Column(db.String(60), nullable=False)
    description = Column(db.String(200), nullable=True)
    private = Column(db.Boolean, nullable=False)

    owner_id = reference_col(User)
    owner = relationship('User', backref='events')

    def __init__(self, **kwargs):
        super().__init__(self, **kwargs)
        self.id = self.generate_id()

    @staticmethod
    def generate_id():
        length = Event.columns.id.type.length
        while True:
            temp_id = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(length))
            if Event.query.get(temp_id) is None:
                break
        return temp_id
