# coding=utf-8
import json
from typing import List, Union

import flask
import flask_mail
import pywebpush

from . import models
from .extensions import db, mail, redis_queue
from .models import MessageTypes
from .views.sse import send_answer, send_message, send_question


@redis_queue.job
def send_email(msg: flask_mail.Message):
    with flask.current_app.app_context():
        mail.send(msg)


@redis_queue.job
def send_push_notification(token: models.WebPushToken, data: Union[dict, list]):
    with flask.current_app.app_context():
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
def notify(message: Union[models.EventMessage, models.Question, models.Answer],
           event: models.Event):  # TODO: get rid of event, replace with message.event
    with flask.current_app.app_context():
        db.session.add_all([message, event])  # Feels kinda hacky. But It Works So Eh.

        if type(message) is models.EventMessage:
            send_message(message)
            subscribers: List[models.Subscription] = event.subscriptions

            if message.type is MessageTypes.TEXT:
                email_subject = "Event Update: {}".format(event.name)
                email_body = "{} : {}".format(message.data['message'], message.timestamp)
                push_data = {
                    "title": event.name,
                    'options': {
                        "timestamp": message.timestamp.timestamp(),
                        "tag": "message-group-{}".format(event.url_id),
                        "body": message.data.get('title', message.data['message']),
                        "actions": [
                            {
                                "action": "view-event",
                                "title": "View Event"
                            }
                        ],
                        "renotify": True,
                        "data": {
                            "url": flask.url_for('events.view_event', token=event.url_id, _external=True,
                                                 _scheme='https')
                        }
                    },
                }  # Possible XSS Attack Vector

            elif message.type is MessageTypes.IMAGE:
                email_subject = "Event Update: {}".format(event.name)
                email_body = "New Image Message: {}".format(message.timestamp)
                push_data = {
                    "title": event.name,
                    'options': {
                        "timestamp": message.timestamp.timestamp(),
                        "tag": "message-group-{}".format(event.url_id),
                        "body": message.data.get('title', "New Image Message"),
                        "actions": [
                            {
                                "action": "view-event",
                                "title": "View Event"
                            }
                        ],
                        "renotify": True,
                        "data": {
                            "url": flask.url_for('events.view_event', token=event.url_id, _external=True,
                                                 _scheme='https')
                        }
                    },
                }

            for subscription in subscribers:
                if subscription.user.email_notify is True:
                    email_message = flask_mail.Message(subject=email_subject,
                                                       recipients=[subscription.user.email],
                                                       html=flask.render_template("email/text_notification.jinja",
                                                                                  text=email_body,
                                                                                  event=event))
                    send_email.queue(email_message)
                if subscription.user.web_push_notify is True:
                    for token in subscription.user.webpush_tokens:
                        send_push_notification.queue(token, push_data)

        elif type(message) is models.Question:
            send_question(message)
            email_subject = "New Question: {}".format(event.name)
            email_body = "{} : {}".format(message.text, message.timestamp)
            push_data = {
                "title": 'New Question: {}'.format(event.name),
                'options': {
                    "timestamp": message.timestamp.timestamp(),
                    "tag": "message-group-{}".format(event.url_id),
                    "body": message.text,
                    "actions": [
                        {
                            "action": "view-event",
                            "title": "View Event"
                        }
                    ],
                    "renotify": True,
                    "data": {
                        "url": flask.url_for('events.view_event', token=event.url_id, _external=True,
                                             _scheme='https')
                    }
                }
            }  # Possible XSS Attack Vector
            if event.owner.email_notify is True:
                email_message = flask_mail.Message(subject=email_subject,
                                                   recipients=[event.owner.email],
                                                   html=flask.render_template("email/text_notification.jinja",
                                                                              text=email_body,
                                                                              event=event))
                send_email.queue(email_message)
            if event.owner.web_push_notify is True:
                for token in event.owner.webpush_tokens:
                    send_push_notification.queue(token, push_data)

        elif type(message) is models.Answer:
            print("Amsreasd")
            send_answer(message)
            email_subject = "Your question has been answered".format(event.name)
            email_body = "{} : {}".format(message.text, message.timestamp)
            push_data = {
                "title": 'Answer to your question: {}'.format(event.name),
                'options': {
                    "timestamp": message.timestamp.timestamp(),
                    "tag": "message-group-{}".format(event.url_id),
                    "body": message.text,
                    "actions": [
                        {
                            "action": "view-event",
                            "title": "View Event"
                        }
                    ],
                    "renotify": True,
                    "data": {
                        "url": flask.url_for('events.view_event', token=event.url_id, _external=True,
                                             _scheme='https')
                    }
                }
            }  # Possible XSS Attack Vector

            if message.questioner.email_notify is True:
                email_message = flask_mail.Message(subject=email_subject,
                                                   recipients=[message.questioner.email],
                                                   html=flask.render_template("email/text_notification.jinja",
                                                                              text=email_body,
                                                                              event=event))
                send_email.queue(email_message)
            if message.questioner.web_push_notify is True:
                for token in message.questioner.webpush_tokens:
                    send_push_notification.queue(token, push_data)
