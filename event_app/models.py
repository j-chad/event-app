# coding=utf-8
import math
import uuid
from datetime import datetime

import flask
import hashids
from bcrypt import gensalt
from flask_login import UserMixin
from sqlalchemy import func
from sqlalchemy.dialects.mysql import DECIMAL, JSON
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property

from .extensions import bcrypt, db
from .utils import MessageTypes

Model = db.Model
Column = db.Column
ForeignKey = db.ForeignKey
relationship = db.relationship


class User(UserMixin, Model):
    __tablename__ = 'users'
    email = Column(db.String(254), primary_key=True)
    subscribed_events = relationship("Subscription", back_populates="user")
    webpush_tokens = relationship('WebPushToken')

    first_name = Column(db.String(40), nullable=False)
    last_name = Column(db.String(40), nullable=True)
    salt = Column(db.Binary(58), nullable=False)
    _password = Column(db.LargeBinary(128), nullable=False)
    email_verified = Column(db.Boolean, nullable=False, default=False)
    session_token = Column(db.String(32), nullable=False, default=lambda: uuid.uuid4().hex)
    created_at = Column(db.DateTime, nullable=False, default=datetime.utcnow)

    latitude = Column(DECIMAL(precision=7, scale=5, unsigned=False), nullable=True)  # -π/2 < latitude < π/2
    longitude = Column(DECIMAL(precision=8, scale=5, unsigned=False), nullable=True)  # -π  < longitude < π

    def __init__(self, first_name: str, email: str, password: str, **kwargs):
        Model.__init__(self, first_name=first_name, email=email, **kwargs)
        self.salt = self.generate_salt()
        self.password = password

    def get_id(self):
        return self.session_token

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
        salted_password = plain_password + self.salt.decode()
        self._password = bcrypt.generate_password_hash(salted_password)

    @hybrid_method
    def check_password(self, plain_password: str) -> bool:
        """Checks If The User Entered The Right Password"""
        salted_password = plain_password + self.salt.decode()
        return bcrypt.check_password_hash(self.password, salted_password)

    @property
    def full_name(self):
        if self.last_name is not None:
            return f"{self.first_name} {self.last_name}"
        else:
            return self.first_name

    @hybrid_property
    def location_enabled(self):
        return (self.latitude is not None) and (self.longitude is not None)

    # noinspection PyComparisonWithNone
    @location_enabled.expression
    def location_enabled(self):
        return (self.latitude != None) & (self.longitude != None)

    @staticmethod
    def generate_salt():
        """Returns a salt which will be stored"""
        return gensalt()

    def __repr__(self):
        return "<User {!r}>".format(self.email, self.full_name)


class Event(Model):
    __tablename__ = 'events'
    id = Column(db.Integer, primary_key=True)
    owner_id = Column(db.String(254), ForeignKey("users.email"), nullable=False)
    owner = relationship('User', backref='events')
    users = relationship("Subscription", back_populates="event")

    name = Column(db.String(60), nullable=False)
    description = Column(db.String(200), nullable=True)
    time = Column(db.DateTime, nullable=True, default=None)
    latitude = Column(DECIMAL(precision=7, scale=5, unsigned=False), nullable=True)  # -π/2 < latitude < π/2
    longitude = Column(DECIMAL(precision=8, scale=5, unsigned=False), nullable=True)  # -π  < longitude < π
    private = Column(db.Boolean, nullable=False, default=False)

    created_at = Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, **kwargs):
        Model.__init__(self, **kwargs)

    def __repr__(self):
        return "<Event {} ({!r})>".format(self.id, self.name)

    @hybrid_property
    def location_enabled(self):
        return (self.latitude is not None) and (self.longitude is not None)

    # noinspection PyComparisonWithNone
    @location_enabled.expression
    def location_enabled(self):
        return (self.latitude != None) & (self.longitude != None)

    @hybrid_method
    def distance_from(self, latitude, longitude):
        return math.acos(
            math.cos(self.latitude)
            * math.cos(latitude)
            * math.cos(self.longitude - longitude)
            + math.sin(self.latitude)
            * math.sin(latitude)
        ) * 6371

    @distance_from.expression
    def distance_from(self, latitude, longitude):
        return func.acos(
            func.cos(self.latitude)
            * func.cos(latitude)
            * func.cos(self.longitude - longitude)
            + func.sin(self.latitude)
            * func.sin(latitude)
        ) * 6371

    @property
    def url_id(self):
        encoder = hashids.Hashids(min_length=10, salt=flask.current_app.config["HASHID_SALT"])
        return encoder.encode(self.id)

    @staticmethod
    def fetch_from_url_token(token: str):
        decoder = hashids.Hashids(min_length=10, salt=flask.current_app.config["HASHID_SALT"])
        id = decoder.decode(token)
        return Event.query.get(id)


class Subscription(Model):
    __tablename__ = 'subscriptions'
    user_id = Column(db.String(254), ForeignKey('users.email'), primary_key=True)
    user = relationship("User", back_populates="subscribed_events")
    event_id = Column(db.Integer, ForeignKey('events.id'), primary_key=True)
    event = relationship("Event", back_populates="users")

    email = Column(db.Boolean, nullable=False, default=False)
    web_push = Column(db.Boolean, nullable=False, default=False)


class WebPushToken(Model):
    __tablename__ = 'webpush_tokens'
    endpoint = Column(db.String(512), primary_key=True)
    user_id = Column(db.String(254), ForeignKey('users.email'), primary_key=True)

    user = relationship("User", back_populates="webpush_tokens")
    p256dh = Column(db.String(100), nullable=False)
    auth = Column(db.String(30), nullable=False)


class Message(Model):
    __tablename__ = 'message'
    id = Column(db.Integer, primary_key=True)
    event_id = Column(db.Integer, ForeignKey('events.id'))
    event = relationship("Event", backref="messages")

    timestamp = Column(db.DateTime, default=datetime.now)
    type = Column(db.Enum(MessageTypes))
    data = Column(JSON)
