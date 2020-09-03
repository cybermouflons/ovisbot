import os
import click
import logging

from itertools import chain
from pymodm import connect
from dotenv import load_dotenv

from ovisbot import __version__
from ovisbot.__main__ import launch
from ovisbot.helpers import draw_options_table
from pymongo.errors import ServerSelectionTimeoutError

load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))

from ovisbot.config import ConfigurableProperty, bot_config  # noqa: E402


@click.group()
@click.option("--env", default="prod", help="Environment to use")
@click.option("--verbose", is_flag=True, default=False, help="Show verbose information")
@click.pass_context
def cli(ctx, env, verbose):
    # if not verbose:
    #     logging.config.dictConfig(config={'version': 1, 'level': logging.NOTSET})
    ctx.ensure_object(dict)
    ctx.obj["env"] = env


@cli.command()
@click.pass_context
def config(ctx):
    """Shows current bot config (Requires DB connection)."""
    try:
        config_cls = bot_config[ctx.obj.get("env")]
        connect(config_cls.DB_URL)
        config = config_cls()
    except ServerSelectionTimeoutError:
        logging.error(
            "Database timeout error! Make use an instance of mongodb is running and your OVISBOT_DB_URL env variable is valid! Terminating... "
        )
        exit(1)

    click.echo(
        draw_options_table(
            chain(
                config._get_configurable_props_from_cls(),
                config._get_static_props_from_cls(),
            )
        )
    )


@cli.command()
@click.pass_context
def setupenv(ctx):
    """Setup environment variables to launch bot"""
    config_cls = bot_config[ctx.obj.get("env")]
    env = {}
    for param in dir(config_cls):
        if param.isupper():
            default = getattr(config_cls, param)
            val = (
                input(
                    "Please enter value for OVISBOT_{0} [default: {1}]:".format(
                        param, default
                    )
                )
                or default
            )
            env[param] = val

    ROOT_DIR = os.path.abspath(os.curdir)

    with open(os.path.join(ROOT_DIR, ".env"), "w") as f:
        for k, v in env.items():
            if not (
                v is None or (isinstance(v, ConfigurableProperty) and v.value is None)
            ):
                f.write("OVISBOT_{0}={1}\n".format(k, v))


@cli.command()
def run():
    """Launch the bot (Require DB connection)"""
    launch()


@cli.command()
def version():
    """Displays bot version"""
    click.echo(f"OvisBot - v{__version__}")
