# coding=utf-8
import click

from . import app, configs, extensions, models


@click.command()
@click.argument('config', default="DevelopmentConfig")
def build_database(config: str) -> None:
    """Builds the database."""
    config_obj = configs.config_map.get(config)
    if config_obj is not None:
        with app.create_app(config_obj).app_context():
            extensions.db.drop_all()
            click.echo("Dropped All Tables")
            extensions.db.create_all()
            click.echo("Created All Tables")
    else:
        raise ValueError("Invalid Config: {}\n\nShould be one of:\n{}".format(
            config, "\n\t".join(configs.config_map.keys())
        ))


@click.command()
@click.argument('config', default="DevelopmentConfig")
def populate_database(config: str) -> None:
    """Adds some data to the database."""
    config_obj = configs.config_map.get(config)
    with app.create_app(config_obj).app_context():
        user_1 = models.User(email='chadfield.jackson@gmail.com', password='password', first_name="Jackson",
                             last_name="Chadfield")
        user_2 = models.User(email='a@example.com', password='password', first_name='John', last_name="Smith")

        event_1 = models.Event(name="My Event", description="super fun", private=False, owner=user_1)
        event_2 = models.Event(name="Public Event", description="also super fun", private=False, owner=user_2)
        event_3 = models.Event(name="Private Event", description="super not fun", private=True, owner=user_2)

        extensions.db.session.add_all((user_1, user_2, event_1, event_2, event_3))
        extensions.db.session.commit()
