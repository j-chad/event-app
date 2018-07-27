# coding=utf-8
import click
import faker

from . import app, configs, extensions, models

fake = faker.Faker()


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
        user_1 = models.User(email='chadfield.jackson@gmail.com',
                             password='password',
                             first_name=fake.first_name_male(),
                             last_name=fake.last_name(),
                             latitude=-36.859385,
                             longitude=174.760502
                             )
        user_2 = models.User(email='a@example.com',
                             password='password',
                             first_name=fake.first_name_male(),
                             last_name=fake.last_name()
                             )

        event_1 = models.Event(name="My Event",
                               description="super fun",
                               private=False,
                               owner=user_1,
                               latitude=-36.882674,
                               longitude=174.753181,
                               start=fake.future_datetime(end_date="+30d")
                               )
        event_2 = models.Event(name="Public Event",
                               description="also super fun",
                               private=False,
                               owner=user_2,
                               latitude=-36.853834,
                               longitude=174.736358,
                               start=fake.future_datetime(end_date="+30d")
                               )
        event_3 = models.Event(name="Private Event",
                               description="super not fun",
                               private=True,
                               owner=user_2,
                               latitude=-36.845867,
                               longitude=174.771034,
                               start=fake.future_datetime(end_date="+30d")
                               )

        extensions.db.session.add_all((user_1, user_2, event_1, event_2, event_3))
        extensions.db.session.commit()
