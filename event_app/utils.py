# coding=utf-8
import enum
import functools
from typing import Callable, Union
from urllib.parse import urljoin, urlparse

import flask
import flask_login
from flask import redirect, request, url_for

from .extensions import db


@enum.unique
class MessageTypes(enum.Enum):
    TEXT = enum.auto()
    # LOCATION = enum.auto()
    # IMAGE = enum.auto()
    # FILE = enum.auto()
    # DATETIME = enum.auto()


def requires_anonymous(endpoint: Union[str, Callable] = "home.index", msg="Already logged in"):
    def decorator(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            if flask_login.current_user.is_authenticated:
                flask.flash(msg, "info")
                return flask.redirect(flask.url_for(endpoint))
            else:
                return func(*args, **kwargs)
        return inner
    return decorator


def redirect_with_next(endpoint, **values) -> flask.Response:
    """Redirect to given endpoint unless alternative given by client"""
    target = request.values.get('next')
    if not target or not is_safe_url(target):
        target = url_for(endpoint, **values)
    return redirect(target)


def is_safe_url(target: str) -> bool:
    """Ensures that a url is safe to redirect to"""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def reference_col(table: db.Model, nullable: bool = False, pk_name: str = 'id', **kwargs) -> db.Column:
    """Column that adds primary key foreign key reference.
    Usage: ::
        category_id = reference_col('category')
        category = relationship('Category', backref='categories')
    """
    return db.Column(
        db.ForeignKey('{0}.{1}'.format(table.__tablename__, pk_name)),
        nullable=nullable, **kwargs
    )
