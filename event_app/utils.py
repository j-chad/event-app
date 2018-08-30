# coding=utf-8
import functools
import os
import uuid
from typing import Callable, Dict, Union
from urllib.parse import urljoin, urlparse

import flask
import flask_login
from PIL import Image
from flask import redirect, request, url_for
from markdown import markdown
from werkzeug.datastructures import FileStorage

from . import models
from .extensions import cleaner


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


def get_unread_messages(user: models.User, count: bool = False) -> Union[
    Dict[str, models.EventMessage], Dict[str, int]]:
    queries = {}
    for subscription in user.subscribed_events:
        queries[subscription.event_id] = []
        queries[subscription.event_id].append(models.EventMessage.query.filter(
                models.EventMessage.timestamp > subscription.last_viewed))
    messages = {}
    if count:
        messages['total'] = 0
    for event_id in queries:
        flat_messages = map(lambda a: a.count() if count else a.all(), queries[event_id])
        quantity = functools.reduce(lambda a, b: a + b, flat_messages)
        messages[event_id] = quantity
        if count:
            messages['total'] += quantity
    return messages


def markdownify(text):
    return cleaner.clean(markdown(text))


def save_image(img: FileStorage) -> str:
    directory = os.path.join(flask.current_app.static_folder, flask.current_app.config['UPLOAD_FOLDER'])
    filename = f"{uuid.uuid4()}.jpeg"
    save_location = os.path.join(directory, filename)

    # Process Image - Maybe Move To Task?
    with Image.open(img.stream) as img_handle:
        if img_handle.height < 100 or img_handle.width < 100:
            raise ValueError("Image Too Small")
        else:
            img_handle.thumbnail((800, img_handle.height), Image.LANCZOS)
            img_handle = img_handle.convert(mode="RGB")  # JPEG has no alpha channel
            img_handle.save(save_location, optimize=True, quality=75)
    return filename
