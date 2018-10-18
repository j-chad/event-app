# coding=utf-8
import base64
import hashlib
from typing import Optional

import flask_login
from flask import abort, request
from flask_sse import ServerSentEventsBlueprint

from .. import models

sse = ServerSentEventsBlueprint('sse', __name__)


@sse.before_request
def check_access():
    if not is_authorised(request.args['channel']):
        abort(403)


sse.add_url_rule(rule="", endpoint="stream", view_func=sse.stream)


def is_authorised(requested_channel: str, user: Optional[models.User] = None) -> bool:
    return flask_login.current_user.is_authenticated and get_channel(user) == requested_channel


def get_channel(user: Optional[models.User] = None):
    if user is None:
        user = flask_login.current_user
    return base64.urlsafe_b64encode(hashlib.sha256(user.email.encode()).digest()).decode()


def send_message(message: models.EventMessage):
    data = {
        "type": message.type.value,
        "data": message.data,
        "event": message.event.url_id
    }
    for subscription in message.event.subscriptions:
        sse.publish(data, channel=get_channel(subscription.user), type="message")


def send_question(question: models.Question):
    data = {
        "id": question.id,
        "question": question.text,
        "event": question.event.url_id
    }
    sse.publish(data, channel=get_channel(question.event.owner), type="question")


def send_answer(answer: models.Answer):
    data = {
        "answer": answer.text,
        "question": {
            "id": answer.question.id
        },
        "event": answer.event.url_id,
        "private": answer.private
    }
    sse.publish(data, channel=get_channel(answer.question.questioner), type="question")
