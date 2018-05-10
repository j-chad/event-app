# coding=utf-8
import flask_login
import flask_mail
from flask_bcrypt import Bcrypt
from flask_debugtoolbar import DebugToolbarExtension
from flask_redis import FlaskRedis
from flask_rq2 import RQ
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
db = SQLAlchemy()
login_manager = flask_login.LoginManager()
mail = flask_mail.Mail()
debug_toolbar = DebugToolbarExtension()
redis_queue = RQ()
redis_store = FlaskRedis()

login_manager.login_view = "users.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"
login_manager.session_protection = "strong"
