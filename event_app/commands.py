# coding=utf-8
import click

from . import app, configs, extensions


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
