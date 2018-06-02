# coding=utf-8
from typing import List

import flask
import flask_mail

from . import models
from .extensions import mail, redis_queue, db
from .utils import MessageTypes


@redis_queue.job
def send_email(msg):
    with flask.current_app.app_context():
        mail.send(msg)


# noinspection PyUnboundLocalVariable
@redis_queue.job
def notify(message: models.Message, event: models.Event):
    with flask.current_app.app_context():
        db.session.add_all([message, event])  # Feels kinda hacky. But It Works So Eh.
        subscribers: List[models.Subscription] = event.users

        if message.type is MessageTypes.TEXT:
            subject = "Event Update: {}".format(event.name)
            email_body = "{} : {}".format(message.data['message'], message.timestamp)

        for subscription in subscribers:
            if subscription.email is True:
                email_message = flask_mail.Message(subject=subject,
                                                   recipients=[subscription.user.email],
                                                   html=flask.render_template("email/text_notification.jinja",
                                                                              text=email_body,
                                                                              event=event))
                send_email.queue(email_message)
            if subscription.web_push is True:
                pass
        db.session.clear(message)
        db.session.clear(event)
