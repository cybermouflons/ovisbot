import gettext
import logging
import os
import pytz
import time

logger = logging.getLogger(__name__)
tz = pytz.timezone("Europe/Athens")
_ = None


def setup_locale():
    global _
    os.environ["TZ"] = "Europe/Athens"
    time.tzset()
    localedir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "locale")
    translate = gettext.translation(
        "ovisbot", localedir, languages=["cy"], fallback=True
    )
    translate.install()
    _ = translate.gettext
