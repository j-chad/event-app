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

    def test_password_rules_invalid_length(self):
        with self.assertRaises(ValueError):
            utils.PasswordRules(uppercase=1, lowercase=1, digits=1, special=1, length=3)
        with self.assertRaises(ValueError):
            utils.PasswordRules(uppercase=4, length=3)
        with self.assertRaises(ValueError):
            utils.PasswordRules(lowercase=4, length=3)
        with self.assertRaises(ValueError):
            utils.PasswordRules(digits=4, length=3)
        with self.assertRaises(ValueError):
            utils.PasswordRules(special=4, length=3)

    def test_password_rules_length(self):
        manager = utils.PasswordRules(length=5)
        with self.subTest("equal"):
            self.assertListEqual(manager.validate("12345"), [])
        with self.subTest("more"):
            self.assertListEqual(manager.validate("123456"), [])
        with self.subTest("less"):
            self.assertListEqual(manager.validate("1234"), ["Password must be at least 5 characters"])

    def test_password_rules_uppercase(self):
        manager = utils.PasswordRules(length=5, uppercase=2)
        with self.subTest("equal"):
            self.assertListEqual(manager.validate("123AA"), [])
        with self.subTest("more"):
            self.assertListEqual(manager.validate("12AAA"), [])
        with self.subTest("less"):
            self.assertListEqual(manager.validate("1234A"), ["Need at least 2 uppercase characters"])
            self.assertListEqual(manager.validate("12345"), ["Need at least 2 uppercase characters"])

    def test_password_rules_lowercase(self):
        manager = utils.PasswordRules(length=5, lowercase=2)
        with self.subTest("equal"):
            self.assertListEqual(manager.validate("123aa"), [])
        with self.subTest("more"):
            self.assertListEqual(manager.validate("12aaa"), [])
        with self.subTest("less"):
            self.assertListEqual(manager.validate("1234a"), ["Need at least 2 lowercase characters"])
            self.assertListEqual(manager.validate("12345"), ["Need at least 2 lowercase characters"])

    def test_password_rules_digits(self):
        manager = utils.PasswordRules(length=5, digits=2)
        with self.subTest("equal"):
            self.assertListEqual(manager.validate("AAA12"), [])
        with self.subTest("more"):
            self.assertListEqual(manager.validate("AA123"), [])
        with self.subTest("less"):
            self.assertListEqual(manager.validate("AAAA1"), ["Need at least 2 digits"])
            self.assertListEqual(manager.validate("AAAAA"), ["Need at least 2 digits"])

    def test_password_rules_special(self):
        manager = utils.PasswordRules(length=5, special=2)
        with self.subTest("equal"):
            self.assertListEqual(manager.validate("123@@"), [])
        with self.subTest("more"):
            self.assertListEqual(manager.validate("12@@@"), [])
        with self.subTest("less"):
            self.assertListEqual(manager.validate("AAAA@"), ["Need at least 2 special characters"])
            self.assertListEqual(manager.validate("AAAAA"), ["Need at least 2 special characters"])
