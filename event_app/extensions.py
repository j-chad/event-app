# coding=utf-8
import bleach
import flask_login
import flask_mail
import markovify
from flask_bcrypt import Bcrypt
from flask_debugtoolbar import DebugToolbarExtension
from flask_humanize import Humanize
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_paranoid import Paranoid
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
limiter = Limiter(key_func=get_remote_address)
paranoid = Paranoid()
humanise = Humanize()

login_manager.login_view = "users.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"
login_manager.session_protection = None

paranoid.redirect_view = "users.login"

fullcleaner = bleach.sanitizer.Cleaner(
        tags=[],
        attributes={},
        protocols=[]
)
cleaner = bleach.sanitizer.Cleaner(
        tags=[
            'a',
            'abbr',
            'acronym',
            'b',
            'blockquote',
            'code',
            'em',
            'i',
            'li',
            'ol',
            'strong',
            'ul',
            'pre',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'hr',
            'p'
        ]
)


class EventNameMarkov(markovify.NewlineText):
    def __init__(self, input_text, state_size=1, *args, **kwargs):
        super().__init__(input_text, state_size, *args, **kwargs)

    def test_sentence_output(self, words, max_overlap_ratio, max_overlap_total) -> bool:
        """Add a length limit"""
        return super().test_sentence_output(words, max_overlap_ratio, max_overlap_total) and len(
            self.word_join(words)) <= 50
