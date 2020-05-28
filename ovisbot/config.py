import logging
import inspect
import sys

from colorama import Fore
from itertools import chain
from typing import Optional, List, Any, NoReturn
from os import environ
from pymodm.errors import ValidationError

from ovisbot.db_models import BotConfig
from ovisbot.helpers import get_props
from texttable import Texttable

logger = logging.getLogger(__name__)


class ConfigurableProperty:
    """Defines a property that can be updated dyanmically
    through the bot. For that purpose, the last value of the property
    is also kept in the database
    """

    def __init__(self, value: str):
        self._value = value

    @property
    def value(self):
        return self._value


class AbstractConfig:
    """Singleton abstract config class"""

    __instance__ = None

    def __new__(cls):
        if AbstractConfig.__instance__ is None:
            logger.info(Fore.YELLOW + "[+]" + Fore.RESET + "Creating config...")
            AbstractConfig.__instance__ = object.__new__(cls)
            AbstractConfig.__instance__._copy_from_class()
            AbstractConfig.__instance__._load_props_from_db()
        return AbstractConfig.__instance__

    def _copy_from_class(self) -> NoReturn:
        """Copies all attributes from class to instance"""
        dynamic_props = self._get_configurable_props_from_cls()
        static_props = self._get_static_props_from_cls()
        for prop, value in chain(dynamic_props, static_props):
            setattr(self, prop, value)

    def _get_or_create_config_from_db(self) -> BotConfig:
        """Loads the BotConfig from DB or creates a new one with the values
        provided in the subclasses of this class

        NOTE: Assumes that there is only one config.
        """
        try:
            return BotConfig.objects.all().first()
        except BotConfig.DoesNotExist:
            config = BotConfig(
                **{k: v for k, v in self._get_configurable_props_from_cls()}
            )
            try:
                config.save()
            except ValidationError as err:
                logger.error("Couldn't launch bot. Not configured properly")
                logger.error(err)
                sys.exit(1)
        return config

    def _load_props_from_db(self) -> NoReturn:
        """Loads properties from config store in the DB. i.e. the configurable options"""
        dynamic_props = self._get_configurable_props_from_cls()
        config_in_db = self._get_or_create_config_from_db()
        self.config_in_db = config_in_db
        for prop, value in dynamic_props:
            saved_value = getattr(config_in_db, prop, None)
            if saved_value is not None and value != saved_value:
                setattr(self, prop, saved_value)

    def _get_configurable_props_from_cls(self) -> List[Any]:
        """Returns configurable properties of class"""
        return map(
            lambda a: (a[0], a[1].value),
            filter(
                lambda a: isinstance(
                    getattr(self.__class__, a[0]), ConfigurableProperty
                ),
                get_props(self.__class__),
            ),
        )

    def _get_static_props_from_cls(self) -> List[Any]:
        """Returns non configurable (static) properties of class"""
        return filter(
            lambda a: not (
                isinstance(getattr(self.__class__, a[0]), ConfigurableProperty)
                or (a[0].startswith("__") and a[0].endswith("__"))
            ),
            get_props(self.__class__),
        )

    def options_table(self) -> str:
        """Returns an ASCII table with configurable options"""
        table = Texttable()
        table.set_deco(Texttable.VLINES | Texttable.HEADER | Texttable.HLINES)
        table.set_cols_dtype(["a", "a"])  # automatic
        table.set_cols_align(["l", "l"])
        table.add_rows(
            [
                ["name", "value"],
                *[
                    [name, getattr(self, name)]
                    for name, val in self._get_configurable_props_from_cls()
                ],
            ]
        )
        return table.draw()

    def save(self) -> NoReturn:
        """Saves current instance config to database"""
        for prop in self._get_configurable_props_from_cls():
            prop_name = prop[0]
            config_in_db_prop_names = list(
                map(lambda p: p[0], get_props(self.config_in_db))
            )
            if prop_name in config_in_db_prop_names:
                setattr(self.config_in_db, prop_name, getattr(self, prop_name))
            else:
                logger.warning(
                    Fore.YELLOW
                    + "Attempted to save configurable config variable ({0}) which is not included in the DB model...".format(
                        prop_name
                    )
                )
        self.config_in_db.save()
        self._load_props_from_db()  # To ensure consistency after db validations


class Config(AbstractConfig):
    """Parent configuration class."""

    DB_URL = environ.get("OVISBOT_DB_URL", "mongodb://mongo/ovisdb")
    COMMAND_PREFIX = environ.get("OVISBOT_COMMAND_PREFIX", "!")
    DISCORD_BOT_TOKEN = environ.get("OVISBOT_DISCORD_TOKEN")

    THIRD_PARTY_COGS_INSTALL_DIR = environ.get(
        "OVISBOT_THIRD_PARTY_COGS_INSTALL_DIR", "/usr/local/share/ovisbot/cogs"
    )
    EXTENSIONS = environ.get("OVISBOT_EXTENSIONS", [])

    COMMAND_CORRECTION_WINDOW = environ.get(
        "OVISBOT_COMMAND_CORRECTION_WINDOW", 30  # time in seconds
    )
    GIT_REPO = environ.get(
        "OVISBOT_GIT_REPO", "https://github.com/apogiatzis/KyriosZolo"
    )

    WOLFRAM_ALPHA_APP_ID = environ.get("OVISBOT_WOLFRAM_ALPHA_APP_ID")
    HTB_CREDS_EMAIL = environ.get("OVISBOT_HTB_CREDS_EMAIL")
    HTB_CREDS_PASS = environ.get("OVISBOT_HTB_CREDS_PASS")

    ADMIN_ROLE = ConfigurableProperty(environ.get("OVISBOT_ADMIN_ROLE"))
    CTFTIME_TEAM_ID = ConfigurableProperty(environ.get("OVISBOT_CTFTIME_TEAM_ID"))
    HTB_TEAM_ID = ConfigurableProperty(environ.get("OVISBOT_HTB_TEAM_ID"))
    REMINDERS_CHANNEL = ConfigurableProperty(environ.get("OVISBOT_REMINDERS_CHANNEL"))
    IS_MAINTENANCE = ConfigurableProperty(environ.get("OVISBOT_IS_MAINTENANCE", False))


class TestingConfig(Config):
    """Configurations for Testing"""

    pass


class DevelopmentConfig(Config):
    """Configurations for Development."""

    pass


class QaConfig(Config):
    """Configurations for QA."""

    pass


class StagingConfig(Config):
    """Configurations for Staging."""

    pass


class ProductionConfig(Config):
    """Configurations for Production."""

    pass


bot_config = {
    "test": TestingConfig,
    "dev": DevelopmentConfig,
    "qa": QaConfig,
    "staging": StagingConfig,
    "prod": ProductionConfig,
}


def get_config():
    return BotConfig.objects.all().first()
