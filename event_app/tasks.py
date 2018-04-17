import flask

from .extensions import mail, redis_queue


@redis_queue.job
def send_email(msg):
    with flask.current_app.app_context():
        mail.send(msg)
