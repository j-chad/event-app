# coding=utf-8
from unittest import TestCase, mock

import event_app
from event_app import app, configs, utils


class TestUtilities(TestCase):

    def test_safe_url(self):
        with event_app.app.create_app(configs.TestingConfig).test_request_context():
            self.assertTrue(utils.is_safe_url("/user"))
            self.assertFalse(utils.is_safe_url("http://badsite.com/user"))
            self.assertFalse(utils.is_safe_url("mal://badsite.com/user"))

    @mock.patch('event_app.utils.url_for')
    def test_redirect_with_next(self, url_for):
        url_for.return_value = "http://localhost/index"
        with self.subTest("Valid Next"):
            with event_app.app.create_app(configs.TestingConfig).test_request_context("/?next=safe"):
                response = utils.redirect_with_next('index')
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.location, "safe")
                self.assertFalse(url_for.called)
        url_for.reset_mock()
        with self.subTest("Invalid Next"):
            with event_app.app.create_app(configs.TestingConfig).test_request_context("/?next=http://badsite.com/a"):
                response = utils.redirect_with_next('index')
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.location, "http://localhost/index")
                self.assertTrue(url_for.called)
