# coding=utf-8
import functools
import os
import random
import uuid
from typing import Callable, Dict, Union
from urllib.parse import urljoin, urlparse

import faker
import flask
import flask_login
from PIL import Image
from flask import redirect, request, url_for
from markdown import markdown
from mdx_downheader import DownHeaderExtension
from werkzeug.datastructures import FileStorage

from . import models
from .extensions import EventNameMarkov, cleaner

fake = faker.Faker()


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
    Dict[models.Event, models.EventMessage], Dict[models.Event, int]]:
    messages = {}
    if count:
        messages['total'] = 0
    for subscription in user.subscribed_events:
        query = models.EventMessage.query.filter(
                models.EventMessage.timestamp > subscription.last_viewed,
                models.EventMessage.event == subscription.event
        )
        if count:
            count = query.count()
            messages[subscription.event] = count
            messages['total'] += count
        else:
            message_list = query.all()
            messages[subscription.event] = message_list
    return messages


def markdownify(text):
    return cleaner.clean(markdown(text, extensions=[DownHeaderExtension(levels=3)]))


def save_image(img: FileStorage) -> str:
    directory = os.path.join(flask.current_app.static_folder, flask.current_app.config['UPLOAD_FOLDER'])
    filename = f"{uuid.uuid4()}.jpeg"
    save_location = os.path.join(directory, filename)

    # Process Image - Maybe Move To Task?
    with Image.open(img.stream) as img_handle:
        if img_handle.height < 100 or img_handle.width < 100:
            raise ValueError("Image Too Small")
        else:
            if img_handle.width < 800:
                width = img_handle.width
            else:
                width = 800
            img_handle.thumbnail((width, img_handle.height), Image.LANCZOS)
            img_handle = img_handle.convert(mode="RGB")  # JPEG has no alpha channel
            img_handle.save(save_location, optimize=True, quality=75)
            img_handle.verify()
    return filename


def event_factory(user: models.User, model: EventNameMarkov):
    while True:
        name = model.make_sentence(tries=1000)
        if name is not None:
            break
    MAX = (-36.837096, 174.927929)
    MIN = (-37.022071, 174.702810)
    lat = random.uniform(MIN[0], MAX[0])
    long = random.uniform(MIN[1], MAX[1])
    return models.Event(name=name,
                        description=fake.paragraph(nb_sentences=5, variable_nb_sentences=True),
                        private=fake.boolean(chance_of_getting_true=20),
                        owner=user,
                        latitude=lat,
                        longitude=long,
                        start=fake.future_datetime(end_date="+40d")
                        )


def user_factory():
    return models.User(email=fake.email(),
                       password='password',
                       first_name=fake.first_name(),
                       last_name=fake.last_name()
                       )


def translate_json_bool(data: str) -> bool:
    normalised = data.lower().strip()
    if normalised == 'true':
        return True
    elif normalised == 'false':
        return False
    else:
        raise ValueError(f"{data} is not true or false")
