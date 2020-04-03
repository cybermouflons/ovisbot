import glob
import logging
import os
import sys

import ovisbot.logger
import ovisbot.locale as i118n

from ovisbot.bot import OvisBot
from ovisbot.core.models import InstalledCogs
from ovisbot.locale import setup_locale


COMMAND_PREFIX = "!"

logger = logging.getLogger(__name__)
token = os.getenv("DISCORD_BOT_TOKEN")
extensions = ["core", "ctf", "manage", "utils", "ctftime", "stats", "poll"]
bot = OvisBot(command_prefix=COMMAND_PREFIX)


def initialize_db():
    cog_names = [
        os.path.basename(f)[:-3]
        for f in glob.glob("./ovisbot/extensions/*.py")
        if os.path.basename(f) != "__init__.py"
    ]
    logger.info(InstalledCogs.objects)
    return cog_names


def launch():
    sys.path.insert(1, os.path.join(os.getcwd(), "ovisbot", "extensions"))
    for extension in extensions:
        bot.load_extension(extension)
    if token is None:
        raise ValueError(i118n._("DISCORD_BOT_TOKEN variable has not been set!"))
    bot.run(token)


def run():
    logger.info("Launching bot....")
    initialize_db()
    setup_locale()
    launch()


if __name__ == "__main__":
    run()
