import flask
import flask_login
from flask_testing import TestCase

from event_app.app import create_app
from event_app.configs import TestingConfig


class TestHomeView(TestCase):

    def create_app(self) -> flask.app.Flask:
        app = create_app(TestingConfig)
        return app

    def test_index_page(self):
        with self.client:
            response = self.client.get(flask.url_for('home.index'))
        self.assert200(response)
        self.assertTrue(flask_login.current_user.is_anonymous)
        self.assertTemplateUsed('home/index_minimal.jinja')
