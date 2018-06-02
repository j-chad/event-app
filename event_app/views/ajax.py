# coding=utf-8
import json

import flask
from flask_login import login_required, current_user

from .. import models, tasks
from ..extensions import db
from ..utils import MessageTypes

ajax = flask.Blueprint('ajax', __name__, url_prefix="/ajax")


@ajax.route('/event/toggle_subscription', methods=("POST",))
@login_required
def toggle_event_subscription():
    token: str = flask.request.form['token']
    event: models.Event = models.Event.fetch_from_url_token(token)
    if event is None:
        flask.abort(404)

    # TODO: implement subscription options. For now, just assume email.
    # email = flask.request.form['email']
    # web_push = flask.request.form['web_push']
    # print(email, web_push)

    if event in current_user.events:
        return flask.jsonify(error="cannot subscribe to own event"), 400
    subscription: models.Subscription = models.Subscription.query.get((current_user.email, event.id))
    if subscription is None:
        sub = models.Subscription(user=current_user, event=event, email=True, web_push=False)
        db.session.add(sub)
        response = flask.jsonify(subscribed=True)
    else:
        db.session.delete(subscription)
        response = flask.jsonify(subscribed=False)
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
