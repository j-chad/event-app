# coding=utf-8
import flask
from flask_testing import TestCase

from event_app import models
from event_app.app import create_app
from event_app.configs import TestingConfig
from event_app.extensions import db, flask_login
from event_app.forms import LoginForm, RegisterForm


class TestUsersView(TestCase):

    def create_app(self) -> flask.app.Flask:
        app = create_app(TestingConfig)
        return app

    def setUp(self):
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_register_page_GET(self):
        response = self.client.get(flask.url_for('users.register'))
        self.assert200(response)
        self.assertTrue(flask_login.current_user.is_anonymous)
        self.assertTemplateUsed('users/register_minimal.jinja')

    def test_register_page_POST_success(self):
        with self.client as c:
            a = RegisterForm()
            response = c.post(flask.url_for('users.register'), data={
                a.first_name.name: "Jackson",
                a.last_name.name : "Chadfield",
                a.email.name     : "chadfield.jackson@gmail.com",
                a.password.name  : "password123"
            }, follow_redirects=True)
            self.assert200(response)
            user_obj = models.User.query.filter_by(email="chadfield.jackson@gmail.com").first()
            self.assertIsNotNone(user_obj)
            self.assertEqual(user_obj, flask_login.current_user)

    def test_register_page_POST_invalid_email(self):
        with self.client as c:
            a = RegisterForm()
            c.post(flask.url_for('users.register'), data={
                a.first_name.name: "Jackson",
                a.last_name.name : "Chadfield",
                a.email.name     : "chadfield.jacksongmail.com",
                a.password.name  : "password123"
            }, follow_redirects=False)
            self.assertIsNone(models.User.query.filter_by(email="chadfield.jacksongmail.com").first())
            self.assertTrue(flask_login.current_user.is_anonymous)
            self.assertTemplateUsed('users/register_minimal.jinja')

    def test_register_page_POST_invalid_first_name(self):
        with self.client as c:
            a = RegisterForm()
            c.post(flask.url_for('users.register'), data={
                a.last_name.name: "Chadfield",
                a.email.name    : "chadfield.jackson@gmail.com",
                a.password.name : "password123"
            }, follow_redirects=False)
            self.assertIsNone(models.User.query.filter_by(email="chadfield.jackson@gmail.com").first())
            self.assertTrue(flask_login.current_user.is_anonymous)
            self.assertTemplateUsed('users/register_minimal.jinja')

    def test_register_page_POST_no_password(self):
        with self.client as c:
            a = RegisterForm()
            c.post(flask.url_for('users.register'), data={
                a.first_name.name: "Jackson",
                a.last_name.name : "Chadfield",
                a.email.name: "chadfield.jackson@gmail.com",
            }, follow_redirects=False)
            self.assertIsNone(models.User.query.filter_by(email="chadfield.jackson@gmail.com").first())
            self.assertTrue(flask_login.current_user.is_anonymous)
            self.assertTemplateUsed('users/register_minimal.jinja')

    def test_login_page_GET(self):
        response = self.client.get(flask.url_for('users.login'))
        self.assert200(response)
        self.assertTrue(flask_login.current_user.is_anonymous)
        self.assertTemplateUsed('users/login_minimal.jinja')

    def test_login_page_POST_success(self):
        with self.client as c:
            a = LoginForm()
            db.session.add(models.User("jackson", "chadfield.jackson@gmail.com", "password123"))
            db.session.commit()
            response = c.post(flask.url_for('users.login'), data={
                a.email.name   : "chadfield.jackson@gmail.com",
                a.password.name: "password123"
            }, follow_redirects=True)
            self.assert200(response)
            user_obj = models.User.query.filter_by(email="chadfield.jackson@gmail.com").first()
            self.assertIsNotNone(user_obj)
            self.assertEqual(user_obj, flask_login.current_user)

    def test_login_page_POST_invalid_email(self):
        with self.client as c:
            a = LoginForm()
            db.session.add(models.User("jackson", "chadfield.jackson@gmail.com", "password123"))
            db.session.commit()
            c.post(flask.url_for('users.login'), data={
                a.email.name   : "chadfield.jacksongmail.com",
                a.password.name: "password123"
            }, follow_redirects=False)
            self.assertIsNone(models.User.query.filter_by(email="chadfield.jacksongmail.com").first())
            self.assertTrue(flask_login.current_user.is_anonymous)
            self.assertTemplateUsed('users/login_minimal.jinja')

    def test_login_page_POST_invalid_password(self):
        with self.client as c:
            a = LoginForm()
            db.session.add(models.User("jackson", "chadfield.jackson@gmail.com", "password123"))
            db.session.commit()
            with self.subTest("wrong password"):
                c.post(flask.url_for('users.login'), data={
                    a.email.name   : "chadfield.jackson@gmail.com",
                    a.password.name: "password12"
                }, follow_redirects=False)
                self.assertIsNone(models.User.query.filter_by(email="chadfield.jacksongmail.com").first())
                self.assertTrue(flask_login.current_user.is_anonymous)
                self.assertTemplateUsed('users/login_minimal.jinja')
            with self.subTest("no password"):
                c.post(flask.url_for('users.login'), data={
                    a.email.name: "chadfield.jackson@gmail.com"
                }, follow_redirects=False)
                self.assertIsNone(models.User.query.filter_by(email="chadfield.jacksongmail.com").first())
                self.assertTrue(flask_login.current_user.is_anonymous)
                self.assertTemplateUsed('users/login_minimal.jinja')