# coding=utf-8
import os
import random

import click
import faker
from flask.cli import with_appcontext

from . import extensions, models, utils

fake = faker.Faker()


@click.command()
@with_appcontext
def build_database() -> None:
    """Builds the database."""
    extensions.db.session.commit()
    extensions.db.drop_all()
    click.secho("Dropped All Tables", fg="red", bold=True)
    extensions.db.create_all()
    click.secho("Created All Tables", fg="green", bold=True)


@click.command()
@with_appcontext
@click.option('--users', default=10, help="Number of Users to generate", type=click.IntRange(0, 50))
@click.option('--events', default=50, help="Number of Events to generate", type=click.IntRange(0, 100))
@click.option('--markov', default='event_name_model.json', help="State file for event naming markov chain")
@click.option('--rebuild/--no-rebuild', default=True)
@click.pass_context
def populate_database(ctx: click.Context, users: int, events: int, rebuild: bool, markov: str) -> None:
    """Adds some data to the database."""

    if rebuild:
        ctx.invoke(build_database)

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

    with click.progressbar(range(users + 2), label="Creating Users", length=users + 2) as bar:
        user_list = [utils.user_factory() for _ in bar]
    user_list += [user_1, user_2]
    bar.update(len(user_list))
    extensions.db.session.add_all(user_list)

    with open(os.path.abspath(markov)) as fp:
        state = fp.read()
    model = extensions.EventNameMarkov.from_json(state)
    click.secho('Loaded Markov Generator', fg="green")
    with click.progressbar(range(events), label="Creating Events") as bar:
        event_list = [utils.event_factory(random.choice(user_list), model=model) for _ in bar]
    extensions.db.session.add_all(event_list)

    extensions.db.session.commit()
    click.secho("Database Updated", fg="green", bold=True)


@click.command()
@click.argument('corpus', type=click.File())
@click.argument('output', type=click.File('w'), default="event_name_model.json")
def generate_markov(corpus, output) -> None:
    data = extensions.EventNameMarkov(corpus.read()).to_json()
    output.write(data)
    click.secho("Markov Chain Generated", fg="green", bold=True)
