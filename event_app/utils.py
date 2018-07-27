# coding=utf-8
import enum
import functools
from typing import Callable, Union
from urllib.parse import urljoin, urlparse

import flask
import flask_login
from flask import redirect, request, url_for


@enum.unique
class MessageTypes(enum.Enum):
    TEXT = 0
    # LOCATION = 1
    # IMAGE = 2
    # FILE = 3


def requires_anonymous(endpoint: Union[str, Callable] = "home.index", msg="You are already logged in"):
    def decorator(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            if flask_login.current_user.is_authenticated:
                flask.flash({"body": msg}, "info")
                return flask.redirect(flask.url_for(endpoint))
            else:
                return func(*args, **kwargs)

        return inner

    return decorator


def redirect_with_next(endpoint: str, **values) -> flask.Response:
    """Redirect to given endpoint unless alternative given by client"""
    target = request.values.get("next")
    if target is None or is_safe_url(target) is False:
        target = url_for(endpoint, **values)
    return redirect(target)


def is_safe_url(target: str) -> bool:
    """Ensures that a url is safe to redirect to"""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def get_unread_messages(user):
    pass
