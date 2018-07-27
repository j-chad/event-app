# coding=utf-8
import json
from typing import List, Union

import flask
import flask_mail
import pywebpush

from . import models
from .extensions import mail, redis_queue, db
from .utils import MessageTypes


@redis_queue.job
def send_email(msg: flask_mail.Message):
    with flask.current_app.app_context():
        mail.send(msg)


@redis_queue.job
def send_push_notification(token: models.WebPushToken, data: Union[dict, list]):
    with flask.current_app.app_context():
        print("Token: {}".format(token))
        try:
            pywebpush.webpush(
                subscription_info={
                    "endpoint": token.endpoint,
                    "keys": {
                        "p256dh": token.p256dh,
                        "auth": token.auth
                    }
                },
                vapid_private_key=flask.current_app.config['WEB_PUSH_PRIVATE_KEY'],
                vapid_claims={
                    "sub": "mailto:chadfield.jackson@gmail.com"
                },
                data=json.dumps(data)
            )
        except pywebpush.WebPushException as e:
            print(e)
            if e.response is not None:
                if e.response.status_code in (404, 410):
                    print('Expired Token, Deleting...')
                    db.session.delete(token)
                    db.session.commit()
                else:
                    raise e
            else:
                raise e


# noinspection PyUnboundLocalVariable
@redis_queue.job
def notify(message: models.EventMessage, event: models.Event):  # TODO: get rid of event, replace with message.event
    with flask.current_app.app_context():
        db.session.add_all([message, event])  # Feels kinda hacky. But It Works So Eh.
        subscribers: List[models.Subscription] = event.users

        if message.type is MessageTypes.TEXT:
            email_subject = "Event Update: {}".format(event.name)
            email_body = "{} : {}".format(message.data['message'], message.timestamp)
            push_data = {
                "title": event.name,
                'options': {
                    "timestamp": message.timestamp.timestamp(),
                    "tag": "message-group-{}".format(message.event.id),
                    "body": message.data["message"],
                    "actions": [
                        {
                            "action": "view-event",
                            "title": "View Event"
                        }
                    ],
                    "renotify": True
                }
            }  # Possible XSS Attack Vector

        for subscription in subscribers:
            if subscription.email is True:
                email_message = flask_mail.Message(subject=email_subject,
                                                   recipients=[subscription.user.email],
                                                   html=flask.render_template("email/text_notification.jinja",
                                                                              text=email_body,
                                                                              event=event))
                send_email.queue(email_message)
            if subscription.web_push is True:
                for token in subscription.user.webpush_tokens:
                    send_push_notification.queue(token, push_data)
