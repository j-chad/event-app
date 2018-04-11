from typing import Counter, Optional

import collections
import wtforms
from wtforms import ValidationError

from .extensions import db


class PasswordRules:
    UPPERCASE = {
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
        'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P',
        'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X',
        'Y', 'Z'
    }
    LOWERCASE = {
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h',
        'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p',
        'q', 'r', 's', 't', 'u', 'v', 'w', 'x',
        'y', 'z'
    }
    DIGITS = {
        '0', '1', '2', '3', '4', '5', '6', '7',
        '8', '9'
    }

    def __init__(self,
                 uppercase: Optional[int] = None,
                 lowercase: Optional[int] = None,
                 digits: Optional[int] = None,
                 special: Optional[int] = None,
                 length: int = 10):
        if uppercase + lowercase + digits + special > length:
            raise ValueError("Length must be >= sum of requirements")
        self.uppercase = uppercase
        self.lowercase = lowercase
        self.digits = digits
        self.special = special
        self.length = length

    def validate(self, password: str, raise_error: bool = False):
        char_count = self.count_characters(password)

        def test(a: int, b: int) -> bool:
            return (a is not None) and (a > b)

        errors = []

        if test(self.uppercase, char_count['uppercase']):
            errors.append("Need at least {} uppercase character{}".format(
                self.uppercase, 's' if self.uppercase != 1 else ''
            ))
        if test(self.lowercase, char_count['lowercase']):
            errors.append("Need at least {} lowercase character{}".format(
                self.lowercase, 's' if self.lowercase != 1 else ''
            ))
        if test(self.digits, char_count['digits']):
            errors.append("Need at least {} digit{}".format(
                self.digits, 's' if self.digits != 1 else ''
            ))
        if test(self.special, char_count['special']):
            errors.append("Need at least {} special character{}".format(
                self.special, 's' if self.special != 1 else ''
            ))
        if test(self.length, char_count['length']):
            errors.append("Password must be at least {} characters".format(self.length))
        if raise_error and errors:
            raise ValidationError(errors[0])
        return errors

    def __call__(self, form: wtforms.Form, field: wtforms.Field):
        return self.validate(field.data, raise_error=True)

    @staticmethod
    def count_characters(password: str) -> Counter[str]:
        counter = collections.Counter(['uppercase', 'lowercase', 'digits', 'special'])
        for char in password:
            if char in PasswordRules.UPPERCASE:
                counter["uppercase"] += 1
            elif char in PasswordRules.LOWERCASE:
                counter["lowercase"] += 1
            elif char in PasswordRules.DIGITS:
                counter["digits"] += 1
            else:
                counter["special"] += 1
        return counter


def reference_col(table: db.Model, nullable: bool = False, pk_name: str = 'id', **kwargs) -> db.Column:
    """Column that adds primary key foreign key reference.
    Usage: ::
        category_id = reference_col('category')
        category = relationship('Category', backref='categories')
    """
    return db.Column(
        db.ForeignKey('{0}.{1}'.format(table.__tablename__, pk_name)),
        nullable=nullable, **kwargs
    )
