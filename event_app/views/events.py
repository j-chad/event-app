# coding=utf-8
from typing import List

import flask
from flask_login import login_required, current_user

from .. import forms, models
from ..extensions import db

events = flask.Blueprint('events', __name__)


@events.route('/discover')
@login_required
def discover() -> flask.Response:
    unowned = models.Event.query.filter(models.Event.owner != current_user).all()
    return flask.render_template("events/index_minimal.jinja",
                                 subscribed=current_user.subscribed_events,
                                 owned=current_user.events, unowned=unowned)


@events.route('/event/create', methods=("GET", "POST"))
@login_required
def create_event() -> flask.Response:
    form = forms.CreateEventForm()
    if form.validate_on_submit():
        new_event = models.Event(owner=current_user,
                                 name=form.name.data,
                                 description=form.description.data,
                                 private=form.private.data)
        db.session.add(new_event)
        db.session.commit()
        return flask.redirect("/event/{}".format(new_event.url_id))
    return flask.render_template("events/create_event_minimal.jinja", form=form)


@events.route('/event/<token>')
@login_required
def view_event(token):
    event: models.Event = models.Event.fetch_from_url_token(token)
    if event is None:
        flask.abort(404)

    subscribed: bool = models.Subscription.query.get((current_user.email, event.id)) is not None
    owner: bool = event in current_user.events
    messages: List[models.Message] = models.Message.query.filter_by(event=event).order_by(
        models.Message.timestamp).all()

    return flask.render_template("events/event_detail_minimal.jinja",
                                 event=event,
                                 subscribed=subscribed,
                                 owner=owner,
                                 messages=messages)
