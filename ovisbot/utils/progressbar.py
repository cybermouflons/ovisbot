# Adopted from https://github.com/Changaco/unicode-progress-bars

import sys
import math

bar_styles = [
    '▁▂▃▄▅▆▇█',
    '⣀⣄⣤⣦⣶⣷⣿',
    '⣀⣄⣆⣇⣧⣷⣿',
    '○◔◐◕⬤',
    '□◱◧▣■',
    '□◱▨▩■',
    '□◱▥▦■',
    '░▒▓█',
    '░█',
    '⬜⬛',
    '▱▰',
    '▭◼',
    '▯▮',
    '◯⬤',
    '⚪⚫',
]


def progressbar(value, max_value=100, barsize=10, style=3, label=""):
    percentage = value / max_value
    progress = round(barsize * percentage)
    empty_progress = barsize - progress
    style_symbols = bar_styles[style % len(bar_styles)]
    full_symbol = style_symbols[-1]
    empty_symbol = style_symbols[0]
    progress_text = [full_symbol] * progress
    empty_text = [empty_symbol] * empty_progress
    percentage_text = "{0}%".format(round(percentage * 100))
    bar = label + " [" + " ".join(progress_text + empty_text) + "] " + percentage_text
    return bar
