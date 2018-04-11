from flask_bcrypt import Bcrypt
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager
from flask_sqlalchemy import Model, SQLAlchemy


class ModelMixin(Model):
    """Mixin that adds convenience methods"""

    def __init__(self, **kwargs):
        pass

    @classmethod
    def create(cls, **kwargs):
        """Create a new record and save it the database."""
        instance = cls(**kwargs)
        return instance.save()

    def update(self, commit: bool = True, **kwargs):
        """Update specific fields of a record."""
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        return commit and self.save() or self

    def save(self, commit: bool = True):
        """Save the record."""
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    def delete(self, commit: bool = True) -> None:
        """Remove the record from the database."""
        db.session.delete(self)
        if commit:
            db.session.commit()


bcrypt = Bcrypt()
db = SQLAlchemy(model_class=ModelMixin)
login_manager = LoginManager()
debug_toolbar = DebugToolbarExtension()

login_manager.login_view = "users.login"
