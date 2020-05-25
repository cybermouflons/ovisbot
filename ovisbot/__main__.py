import logging
import ovisbot.utils.logging

from colorama import init as colorama_init

from ovisbot.locale import setup_locale
from ovisbot.bot import OvisBot

logger = logging.getLogger(__name__)


def run():
    colorama_init(autoreset=True)
    setup_locale()

    bot = OvisBot()
    bot.launch()


if __name__ == "__main__":
    run()
