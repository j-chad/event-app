# coding=utf-8
import math
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Any, Dict

import flask
import hashids
import jinja2
from bcrypt import gensalt
from flask_login import UserMixin
from sqlalchemy import func
from sqlalchemy.dialects.mysql import DECIMAL, JSON
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property

from .extensions import bcrypt, db
from .utils import MessageTypes

Model = db.Model
Column = db.Column
ForeignKey = db.ForeignKey
relationship = db.relationship


# noinspection PyMethodParameters,PyUnresolvedReferences,PyReturnFromInit
class CommonMixin:
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    @declared_attr
    def __init__(cls):
        def inner(*args, **kwargs):
            Model.__init__(*args, **kwargs)

        return inner


class User(CommonMixin, UserMixin, Model):
    email: str = Column(db.String(254), primary_key=True)
    subscribed_events: List['Subscription'] = relationship("Subscription", back_populates="user")
    webpush_tokens: List['WebPushToken'] = relationship('WebPushToken')

    first_name: str = Column(db.String(40), nullable=False)
    last_name: str = Column(db.String(40), nullable=True)
    salt = Column(db.Binary(58), nullable=False)
    _password = Column(db.LargeBinary(128), nullable=False)
    email_verified: bool = Column(db.Boolean, nullable=False, default=False)
    session_token: str = Column(db.String(32), nullable=False, default=lambda: uuid.uuid4().hex)
    created_at: datetime = Column(db.DateTime, nullable=False, default=datetime.utcnow)

    latitude: Decimal = Column(DECIMAL(precision=7, scale=5, unsigned=False), nullable=True)  # -90 < latitude < 90
    longitude: Decimal = Column(DECIMAL(precision=8, scale=5, unsigned=False), nullable=True)  # -180  < longitude < 180

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
    def full_name(self) -> str:
        if self.last_name is not None:
            return f"{self.first_name} {self.last_name}"
        else:
            return self.first_name

    @hybrid_property
    def location_enabled(self) -> bool:
        return (self.latitude is not None) and (self.longitude is not None)

    # noinspection PyComparisonWithNone
    @location_enabled.expression
    def location_enabled(self) -> bool:
        return (self.latitude != None) & (self.longitude != None)

    @staticmethod
    def generate_salt():
        """Returns a salt which will be stored"""
        return gensalt()


class Event(CommonMixin, Model):
    id: int = Column(db.Integer, primary_key=True)
    owner_id: str = Column(db.String(254), ForeignKey("user.email"), nullable=False)
    owner: User = relationship('User', backref='events')
    users: List["Subscription"] = relationship("Subscription", back_populates="event")

    name: str = Column(db.String(60), nullable=False)
    description: str = Column(db.String(200), nullable=True)
    start: datetime = Column(db.DateTime, nullable=True, default=None)
    latitude: Decimal = Column(DECIMAL(precision=7, scale=5, unsigned=False), nullable=True)  # -90 < latitude < 90
    longitude: Decimal = Column(DECIMAL(precision=8, scale=5, unsigned=False), nullable=True)  # -180  < longitude < 180
    private: bool = Column(db.Boolean, nullable=False, default=False)

    created_at: datetime = Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @hybrid_property
    def location_enabled(self) -> bool:
        return (self.latitude is not None) and (self.longitude is not None)

    # noinspection PyComparisonWithNone
    @location_enabled.expression
    def location_enabled(self) -> bool:
        return (self.latitude != None) & (self.longitude != None)

    @hybrid_method
    def distance_from(self, latitude: Decimal, longitude: Decimal) -> float:
        return math.acos(
            math.cos(math.radians(self.latitude))
            * math.cos(math.radians(latitude))
            * math.cos(math.radians(self.longitude) - math.radians(longitude))
            + math.sin(math.radians(self.latitude))
            * math.sin(math.radians(latitude))
        ) * 6371

    @distance_from.expression
    def distance_from(self, latitude: Decimal, longitude: Decimal) -> float:
        return func.acos(
            func.cos(func.radians(self.latitude))
            * func.cos(func.radians(latitude))
            * func.cos(func.radians(self.longitude) - func.radians(longitude))
            + func.sin(func.radians(self.latitude))
            * func.sin(func.radians(latitude))
        ) * 6371

    @property
    def url_id(self) -> str:
        encoder = hashids.Hashids(min_length=10, salt=flask.current_app.config["HASHID_SALT"])
        return encoder.encode(self.id)

    @staticmethod
    def fetch_from_url_token(token: str) -> 'Event':
        decoder = hashids.Hashids(min_length=10, salt=flask.current_app.config["HASHID_SALT"])
        id = decoder.decode(token)
        return Event.query.get(id)


class Subscription(CommonMixin, Model):
    user_id: str = Column(db.String(254), ForeignKey('user.email'), primary_key=True)
    user: User = relationship("User", back_populates="subscribed_events")
    event_id: int = Column(db.Integer, ForeignKey('event.id'), primary_key=True)
    event: Event = relationship("Event", back_populates="users")

    email: bool = Column(db.Boolean, nullable=False, default=False)
    web_push: bool = Column(db.Boolean, nullable=False, default=False)


class WebPushToken(CommonMixin, Model):
    endpoint: str = Column(db.String(512), primary_key=True)
    user_id: str = Column(db.String(254), ForeignKey('user.email'), primary_key=True)

    user: User = relationship("User", back_populates="webpush_tokens")
    p256dh: str = Column(db.String(100), nullable=False)
    auth: str = Column(db.String(30), nullable=False)


class EventMessage(CommonMixin, Model):
    id: int = Column(db.Integer, primary_key=True)
    event_id: int = Column(db.Integer, ForeignKey('event.id'))
    event: Event = relationship("Event", backref="messages")

    timestamp: datetime = Column(db.DateTime, default=datetime.now)
    type: MessageTypes = Column(db.Enum(MessageTypes))
    data: Dict[str, Any] = Column(JSON)

    def render(self, class_=None) -> str:
        """Renders the message for display"""

        if class_ is None:
            class_ = []

        if self.type is MessageTypes.TEXT:
            data = jinja2.escape(self.data['message'])
            class_.append('text')
            return f"<div class='{' '.join(class_)}' data-timestamp={self.timestamp.isoformat()}>{data}</div>"


class Answer(CommonMixin, Model):
    id: int = Column(db.Integer, primary_key=True)
    event_id: int = Column(db.Integer, ForeignKey('event.id'))
    event: Event = relationship("Event", backref="answers")

    question = relationship("Question", uselist=False, back_populates="answer")
    timestamp: datetime = Column(db.DateTime, default=datetime.now)
    text: str = Column(db.String(300), nullable=False)


class Question(CommonMixin, Model):
    id: int = Column(db.Integer, primary_key=True)
    event_id: int = Column(db.Integer, ForeignKey('event.id'))
    event: Event = relationship("Event", backref="questions")

    answer_id = Column(db.Integer, ForeignKey('answer.id'), nullable=True, default=None, unique=True)
    answer: EventMessage = relationship('Answer')

    timestamp: datetime = Column(db.DateTime, default=datetime.now)
    text: str = Column(db.String(100), nullable=False)
