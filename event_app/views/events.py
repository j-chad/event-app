# coding=utf-8

import flask
from flask_login import login_required, current_user

from .. import forms, models
from ..extensions import db

events = flask.Blueprint('events', __name__)


@events.route('/event')
@login_required
def home() -> flask.Response:
    return flask.render_template("events/index_minimal.jinja", events=current_user.subscribed_events)


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
    return flask.render_template("events/event_detail_minimal.jinja", event=event)
