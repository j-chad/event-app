# coding=utf-8
import json

import flask
from flask_login import login_required, current_user

from .. import models, tasks
from ..extensions import db
from ..utils import MessageTypes

ajax = flask.Blueprint('ajax', __name__, url_prefix="/ajax")


@ajax.route('/event/update_subscription', methods=("POST",))
@login_required
def update_event_subscription():
    data: dict = flask.request.json
    event: models.Event = models.Event.fetch_from_url_token(data['token'])
    if event is None:
        flask.abort(404)

    email: bool = bool(data['email'])
    push: bool = bool(data['push'])

    if event in current_user.events:
        return flask.jsonify(error="Cannot subscribe to own event"), 400
    subscription: models.Subscription = models.Subscription.query.get((current_user.email, event.id))

    if email is False and push is False:
        if subscription is None:
            return flask.jsonify(email=False, push=False)  # Already Unsubscribed - Update Client
        db.session.delete(subscription)
        response = flask.jsonify(email=False, push=False)  # Unsubscribe
    else:
        if subscription is None:
            sub = models.Subscription(user=current_user, event=event, email=email, web_push=push)
            db.session.add(sub)
            response = flask.jsonify(email=email, push=push)  # Create Subscription
        else:
            subscription.web_push = push
            subscription.email = email
            response = flask.jsonify(email=email, push=push)
    db.session.commit()
    return response


@ajax.route('/event/add_message', methods=("POST",))
@login_required
def event_add_message():
    token: str = flask.request.form['token']
    try:
        type_: MessageTypes = {'text': MessageTypes.TEXT}[flask.request.form['type']]
    except KeyError:  # If not valid type
        flask.abort(400)
    try:
        data: dict = json.loads(flask.request.form['data'])
    except ValueError:  # If not valid JSON
        flask.abort(400)
    event: models.Event = models.Event.fetch_from_url_token(token)
    if event is None:
        flask.abort(400)  # If not valid event token

    # noinspection PyUnboundLocalVariable
    message = models.Message(event=event, type=type_, data=data)
    db.session.add(message)
    db.session.commit()

    tasks.notify.queue(message, event)

    return "Ok", 200


@ajax.route('/user/save_webpush', methods=("POST",))
@login_required
def save_web_push_data():
    data = flask.request.json
    try:
        endpoint = data['endpoint']
        p256dh = data['keys']['p256dh']
        auth = data['keys']['auth']
    except KeyError:
        flask.abort(400)

    # noinspection PyUnboundLocalVariable
    token = models.WebPushToken(user=current_user,
                                endpoint=endpoint,
                                p256dh=p256dh,
                                auth=auth)
    db.session.add(token)
    db.session.commit()
    return 'Ok', 200
