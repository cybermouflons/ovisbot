import gettext
import logging
import os

logger = logging.getLogger(__name__)
_ = None


def setup_locale():
    global _
    localedir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "locale")
    translate = gettext.translation(
        "ovisbot", localedir, languages=["cy"], fallback=True
    )
    translate.install()
    _ = translate.gettext
    logger.info(_)
