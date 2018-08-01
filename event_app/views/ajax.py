# coding=utf-8
import decimal
from secrets import token_urlsafe

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
    return flask.jsonify(payload)


@ajax.route('/event/update_subscription', methods=("POST",))
@login_required
def update_subscription():
    event: models.Event = models.Event.fetch_from_url_token(flask.request.form['token'])
    if event is None:
        flask.abort(404)

    if event in current_user.events:
        return flask.jsonify(error="Cannot subscribe to own event"), 400
    subscription: models.Subscription = models.Subscription.query.get((current_user.email, event.id))

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
        type_: MessageTypes = MessageTypes(int(flask.request.form['type']))
        print(type)
    except (KeyError, ValueError):  # If not valid type
        flask.abort(400)
    event: models.Event = models.Event.fetch_from_url_token(token)
    if event is None:
        flask.abort(400)  # If not valid event token
    else:
        if event.owner != flask_login.current_user:
            flask.abort(403)

    # noinspection PyUnboundLocalVariable
    if type_ is MessageTypes.TEXT:
        data = {"message": flask.request.form['message']}

    # noinspection PyUnboundLocalVariable
    message = models.EventMessage(event=event, type=type_, data=data)
    db.session.add(message)
    db.session.commit()

    tasks.notify.queue(message, event)

    return "Ok", 200


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

    question = models.Question(event=event, text=flask.request.form['message'])
    db.session.add(question)
    db.session.commit()

    tasks.notify.queue(question, event)
    return "Ok"


@ajax.route('/user/save_webpush', methods=("POST",))
@login_required
def save_web_push():
    print('Saved New Webpush')
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
