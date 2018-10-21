# coding=utf-8
import decimal
import uuid
from secrets import token_urlsafe
from typing import Optional

import flask
import flask_login
from flask_login import current_user, login_required

from event_app.models import MessageTypes
from .. import forms, models, tasks, utils
from ..extensions import db, redis_store
from ..views.users import send_validation_email

ajax = flask.Blueprint('ajax', __name__, url_prefix="/ajax")


@ajax.route('/user/register', methods=("POST",))
@utils.requires_anonymous()
def register_user():
    register_form = forms.RegisterForm()
    if register_form.validate_on_submit():
        user = models.User(first_name=register_form.first_name.data,
                           last_name=register_form.last_name.data,
                           email=register_form.email.data,
                           password=register_form.password.data)
        db.session.add(user)
        db.session.commit()
        flask_login.login_user(user)
        token = str(token_urlsafe())
        redis_store.set('USER:VERIFICATION_TOKEN#{}'.format(token), user.email,
                        ex=flask.current_app.config['VERIFICATION_TOKEN_EXPIRY'],
                        nx=True)
        send_validation_email(user, token)
        flask.flash({"body": "Please check your email"}, "info")
        payload = {"status": "success"}
    else:
        payload = {
            "status": "error",
            "errors": {
                "f_name": register_form.first_name.errors,
                "l_name": register_form.last_name.errors,
                "email": register_form.email.errors,
                "password": register_form.password.errors,
                "confirm": register_form.confirm_password.errors,
                "main": []
            }
        }
    return flask.jsonify(payload), 201


@ajax.route('/user/update_settings', methods=("POST",))
@login_required
def update_settings():
    current_user: models.User = flask_login.current_user
    password = flask.request.form.get('password', None)
    f_name = flask.request.form.get('f_name', None)
    l_name = flask.request.form.get('l_name', None)
    email = flask.request.form.get('email', None)
    push_notif = flask.request.form.get('push_notif', None)
    email_notif = flask.request.form.get('email_notif', None)

    if f_name is not None:
        current_user.first_name = f_name
    if l_name is not None:
        current_user.last_name = l_name
    if push_notif is not None:
        current_user.web_push_notify = utils.translate_json_bool(push_notif)
    if email_notif is not None:
        current_user.email_notify = utils.translate_json_bool(email_notif)
    if email is not None:
        current_user.email = email
        current_user.email_verified = False
        token = str(token_urlsafe())
        redis_store.set('USER:VERIFICATION_TOKEN#{}'.format(token), email,
                        ex=flask.current_app.config['VERIFICATION_TOKEN_EXPIRY'],
                        nx=True)
        send_validation_email(current_user, token)
    if password is not None:
        old_pass = flask.request.form.get('old_password')
        if old_pass is None:
            flask.abort(401)
        if not current_user.check_password(old_pass):
            flask.abort(403)
        current_user.password = password
        flask_login.logout_user()
        current_user.session_token = uuid.uuid4().hex
    db.session.commit()

    return "", 204


@ajax.route('/event/update_subscription', methods=("POST",))
@login_required
def update_subscription():
    event: models.Event = models.Event.fetch_from_url_token(flask.request.form['token'])
    if event is None:
        flask.abort(404)

    if event in current_user.events:
        return flask.jsonify(error="Cannot subscribe to own event"), 400
    subscription: models.Subscription = models.Subscription.query.get((current_user.id, event.id))

    # Toggle Subscription
    if subscription is None:
        sub = models.Subscription(user=current_user, event=event)
        db.session.add(sub)
    else:
        db.session.delete(subscription)

    db.session.commit()
    return flask.jsonify(subscribed=(subscription is None))


@ajax.route('/event/add_message', methods=("POST",))
@login_required
def event_add_message():
    token: str = flask.request.form['token']
    try:
        type_: MessageTypes = MessageTypes(flask.request.form['type'])
    except (KeyError, ValueError):  # If not valid type
        flask.abort(400)
    event: models.Event = models.Event.fetch_from_url_token(token)
    if event is None:
        flask.abort(400)  # If not valid event token
    else:
        if event.owner != flask_login.current_user:
            flask.abort(403)

    title: Optional[str] = flask.request.form.get('title', None)

    if title is not None:
        title = title.strip()
        if len(title) == 0:
            title = None

    # noinspection PyUnboundLocalVariable
    if type_ is MessageTypes.TEXT:
        message: str = flask.request.form['message']

        if len(message.strip()) == 0:
            flask.abort(400)

        data = {
            "title": title,
            "message": utils.markdownify(message)
        }

    elif type_ is MessageTypes.IMAGE:
        image = flask.request.files['image']
        if len(image.filename) == 0 or \
                image.mimetype not in flask.current_app.config['ALLOWED_IMAGE_MIMETYPES']:
            flask.abort(400)
        name = utils.save_image(image)
        data = {"file": name, "title": title}
    else:  # Unknown Type
        flask.abort(400)

    # noinspection PyUnboundLocalVariable
    message = models.EventMessage(event=event, type=type_, data=data)
    db.session.add(message)
    db.session.commit()

    tasks.notify.queue(message, event)
    return "Ok", 201


@ajax.route('/event/remove_message', methods=("POST",))
@login_required
def event_remove_message():
    id: str = flask.request.form['id']
    try:
        int_id = int(id)
    except ValueError:
        flask.abort(400)

    message: models.EventMessage = models.EventMessage.query.get(int_id)
    if message is None:
        flask.abort(400)  # If not valid message id
    else:
        if message.event.owner != flask_login.current_user:
            flask.abort(403)

    db.session.delete(message)
    db.session.commit()
    return '', 204


@ajax.route('/event/update_viewed_messages', methods=("POST",))
@login_required
def event_viewed_message():
    event_id: str = flask.request.form['event']
    event: models.Event = models.Event.fetch_from_url_token(event_id)
    if event is None:
        flask.abort(400)  # If not valid event token

    subscription: models.Subscription = models.Subscription.query.get((flask_login.current_user.id, event.id))
    if subscription is None:
        flask.abort(400)

    subscription.update()

    return '', 204


@ajax.route('/event/add_question', methods=("POST",))
@login_required
def event_add_question():
    token: str = flask.request.form['token']
    event: models.Event = models.Event.fetch_from_url_token(token)
    if event is None:
        flask.abort(400)
    else:
        if event.owner == flask_login.current_user:
            flask.abort(400)

    question = models.Question(event=event, text=flask.request.form['message'],
                               questioner=current_user)
    db.session.add(question)
    db.session.commit()

    tasks.notify.queue(question, event)
    return "Ok", 201


@ajax.route('/event/add_answer', methods=("POST",))
@login_required
def event_add_answer():
    question_id: str = flask.request.form['question']
    reply: str = flask.request.form['reply'].strip()
    private: bool = flask.request.form.get('private') is not None

    question: Optional[models.Question] = models.Question.query.get(question_id)

    if question is None:
        flask.abort(400)
    if len(reply) == 0:
        flask.abort(400)
    if flask_login.current_user != question.event.owner:
        flask.abort(403)

    answer = models.Answer(question=question, text=reply, private=private)
    db.session.add(answer)
    db.session.commit()

    tasks.notify.queue(answer, question.event)
    return "Ok", 201


@ajax.route('/user/save_webpush', methods=("POST",))
@login_required
def save_web_push():
    data = flask.request.json
    try:
        endpoint = data['endpoint']
        p256dh = data['keys']['p256dh']
        auth = data['keys']['auth']
    except KeyError:
        return flask.abort(400)

    if models.WebPushToken.query.get(endpoint) is not None:
        return "Not Saved", 202

    token = models.WebPushToken(user=current_user,
                                endpoint=endpoint,
                                p256dh=p256dh,
                                auth=auth)
    db.session.add(token)
    db.session.commit()
    return 'Ok', 201


@ajax.route('/user/settings/update_location', methods=("POST",))
@login_required
def update_location():
    latitude = decimal.Decimal(flask.request.form['lat'])
    longitude = decimal.Decimal(flask.request.form['lng'])
    if -90 <= latitude <= 90 and -180 <= longitude <= 180:
        current_user.latitude = latitude
        current_user.longitude = longitude
        db.session.commit()
        return "Ok", 200
    else:
        flask.abort(400)


@ajax.route('/events')
def get_events():
    lat = decimal.Decimal(flask.request.args['lat'])
    lng = decimal.Decimal(flask.request.args['lng'])

    events = models.Event.query.filter_by(
            models.Event.distance_from(lat, lng) <= flask.current_app.config['EVENT_MAXIMUM_DISTANCE']
    ).order_by(
            models.Event.distance_from(lat, lng),
            models.Event.time
    ).all()

    return_value = []
    for event in events:
        return_value.append({
            'name': event.name,
            'coords': {
                'lat': event.latitude,
                'lng': event.longitude
            },
            'owner': {
                'name': event.owner.full_name,
            }
        })
    return flask.jsonify(return_value)
