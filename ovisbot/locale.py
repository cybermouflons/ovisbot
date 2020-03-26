import gettext
import logging
import os

_ = None


def setup_locale():
    global _
    localedir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'locale')
    translate = gettext.translation('ovisbot', localedir, fallback=True)
    _ = translate.gettext
