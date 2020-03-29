import logging
import ovisbot.logger

from ovisbot.core import launch
from ovisbot.locale import setup_locale

logger = logging.getLogger(__name__)


def run():
    logger.info("Launching bot....")
    setup_locale()
    launch()


if __name__ == "__main__":
    run()
