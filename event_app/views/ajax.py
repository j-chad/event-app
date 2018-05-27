# coding=utf-8
import flask
from flask_login import login_required, current_user

from .. import models
from ..extensions import db

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
