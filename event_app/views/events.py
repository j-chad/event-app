# coding=utf-8
from typing import List

import flask
from flask_login import current_user, login_required
from sqlalchemy import or_

from event_app.models import MessageTypes
from .. import forms, models, utils
from ..extensions import db

events = flask.Blueprint('events', __name__)


# noinspection PyCallByClass
@events.route('/discover')
@login_required
def discover() -> flask.Response:
    if current_user.location_enabled:
        _distance_query = models.Event.distance_from(current_user.latitude, current_user.longitude)
    else:
        _distance_query = None  # Reference to allow dictionary use

    # Order
    order_preference = [_distance_query, "start", "name"]
    order_by_string = flask.request.args.get('order')
    if order_by_string is not None:
        if order_by_string == "time":
            order = "start"
        elif order_by_string == "name":
            order = "name"
        elif order_by_string == "distance" and current_user.location_enabled:
            order = _distance_query
        else:
            return flask.abort(400)

        # Prioritise selected order
        order_preference.remove(order)
        order_preference.insert(0, order)
    # Remove None From Priority List
    order_preference[:] = [x for x in order_preference if x is not None]

    # Distance
    distance_param = flask.request.args.get('dist', 'far')
    if distance_param == "far":
        max_distance = flask.current_app.config['DEFAULT_EVENT_MAXIMUM_DISTANCE']
    elif distance_param == "medium":
        max_distance = flask.current_app.config['DEFAULT_EVENT_MEDIUM_DISTANCE']
    elif distance_param == "nearby":
        max_distance = flask.current_app.config['DEFAULT_EVENT_NEARBY_DISTANCE']
    elif distance_param == "all":
        max_distance = None
    else:
        return flask.abort(400)

    if current_user.location_enabled and max_distance is not None:
        events_ = models.Event.query.filter(
                models.Event.distance_from(current_user.latitude, current_user.longitude) <= max_distance,
                models.Event.private == False
        ).order_by(*order_preference).all()
    else:
        events_ = models.Event.query.filter(
                models.Event.private == False
        ).order_by(*order_preference).all()

    return flask.render_template("events/discover.jinja", events=events_)


@events.route('/event/create', methods=("GET", "POST"))
@login_required
def create_event() -> flask.Response:
    form = forms.CreateEventForm()
    if form.validate_on_submit():

        description = form.description.data
        if description is not None:
            if len(description.strip()) == 0:
                description = None
            else:
                description = utils.markdownify(description)

        new_event = models.Event(owner=current_user,
                                 name=form.name.data,
                                 description=description,
                                 private=form.private.data,
                                 start=form.start.data,
                                 latitude=form.latitude.data,
                                 longitude=form.longitude.data)
        db.session.add(new_event)
        db.session.commit()
        return flask.redirect("/event/{}".format(new_event.url_id))
    return flask.render_template("events/create.jinja", form=form)


# noinspection PyPep8
@events.route('/event/<token>')
@login_required
def view_event(token):
    event: models.Event = models.Event.fetch_from_url_token(token)
    if event is None:
        flask.abort(404)

    subscription: models.Subscription = models.Subscription.query.get((current_user.id, event.id))
    subscribed: bool = subscription is not None
    if subscribed:
        subscription.update()

    owner: bool = event in current_user.events
    messages: List[models.EventMessage] = models.EventMessage.query.filter_by(event=event).order_by(
            models.EventMessage.timestamp.desc()).all()
    # noinspection PyComparisonWithNone
    answered_questions: List[models.Question] = models.Question.query.filter(
            models.Question.event == event,
            models.Question.answer != None,
            or_(
                    models.Question.answer.has(private=False),
                    models.Question.questioner == current_user
            )
    ).order_by(models.Question.timestamp.desc()).all()

    base_kwargs = {
        "event": event,
        "user": current_user,
        "messages": messages,
    }

    if owner:

        unanswered_questions = models.Question.query.filter_by(event=event, answer=None).all()
        unanswered_question_count = len(unanswered_questions)

        return flask.render_template("events/event_detail.jinja",
                                     **base_kwargs,
                                     owner=True,
                                     message_types=MessageTypes,
                                     unanswered_question_count=unanswered_question_count,
                                     unanswered_questions=unanswered_questions,
                                     answered_questions=answered_questions)
    else:
        unanswered_question_count = models.Question.query.filter_by(event=event, answer=None,
                                                                    questioner=current_user).count()

        return flask.render_template("events/event_detail.jinja",
                                     **base_kwargs,
                                     subscribed=subscribed,
                                     owner=False,
                                     unanswered_question_count=unanswered_question_count,
                                     answered_questions=answered_questions)


@events.route('/event/<token>/questions')
@login_required
def questions(token):
    event: models.Event = models.Event.fetch_from_url_token(token)
    if event is None:
        flask.abort(404)

    if event not in current_user.events:
        flask.abort(403)

    _questions: List[models.Question] = models.Question.query.filter_by(
            event=event, answer=None
    ).order_by(models.Question.timestamp).all()

    return flask.render_template("events/questions.jinja",
                                 event=event,
                                 questions=_questions
                                 )
