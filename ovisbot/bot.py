import os
import discord
import sys
import logging
import ovisbot.locale as i18n

from discord.ext.commands import Bot
from dotenv import load_dotenv
from pathlib import Path
from os import environ
from typing import NoReturn
from pymodm import connect
from pymongo.errors import ServerSelectionTimeoutError
from colorama import Fore

from ovisbot import __version__
from ovisbot import commands
from ovisbot.cog_manager import CogManager
from ovisbot.events import hook_events
from ovisbot.error_handling import hook_error_handlers
from ovisbot.commands.base import BaseCommandsMixin
from ovisbot.commands.rank import RankCommandsMixin
from ovisbot.commands.manage import ManageCommandsMixin
from discord.ext.commands.errors import ExtensionNotFound

logger = logging.getLogger(__name__)


class OvisBot(Bot, BaseCommandsMixin, RankCommandsMixin, ManageCommandsMixin):
    def __init__(self, *args, **kwargs):
        # Load Config
        env_path = os.path.join(
            Path(sys.modules[__name__].__file__).resolve().parent.parent, ".env"
        )
        load_dotenv(dotenv_path=env_path, verbose=True)
        env = environ.get("OVISBOT_ENV", "dev")
        from ovisbot.config import bot_config

        try:
            self.config_cls = bot_config[env]
            self.init_db()
            self.config = self.config_cls()
        except ServerSelectionTimeoutError:
            logging.error(
                "Database timeout error! Make use an instance of mongodb is running and your OVISBOT_DB_URL env variable is valid! Terminating... "
            )
            exit(1)

        super().__init__(*args, command_prefix=self.config.COMMAND_PREFIX, **kwargs)

        # Perform necessary tasks
        Path(self.config.THIRD_PARTY_COGS_INSTALL_DIR).mkdir(
            parents=True, exist_ok=True
        )

        # Hook commands
        BaseCommandsMixin.load_commands(self)
        RankCommandsMixin.load_commands(self)
        ManageCommandsMixin.load_commands(self)

        # Error Handling & Events
        hook_error_handlers(self)
        hook_events(self)

        # Load Cogs
        try:
            self.cog_manager = CogManager(self)
            self.cog_manager.load_cogs()
        except ExtensionNotFound:
            pass

    def launch(self) -> None:
        logger.info("Launching bot...")

        if self.config.DISCORD_BOT_TOKEN is None:
            raise ValueError(i18n._("DISCORD_BOT_TOKEN variable has not been set!"))
        self.run(self.config.DISCORD_BOT_TOKEN)

    def init_db(self) -> NoReturn:
        """Initializes db connection"""
        connect(self.config_cls.DB_URL)
