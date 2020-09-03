import inspect
import requests
import os
import urllib.parse

from discord.ext.commands.core import GroupMixin
from texttable import Texttable


def chunkify(text, limit):
    chunks = []
    while len(text) > limit:
        idx = text.index("\n", limit)
        chunks.append(text[:idx])
        text = text[idx:]
    chunks.append(text)
    return chunks


def escape_md(text):
    return text.replace("_", "\_").replace("*", "\*").replace(">>>", "\>>>")


def create_corimd_notebook():
    base_url = "https://notes.status.im/"
    create_new_note_url = base_url + "new"
    res = requests.get(create_new_note_url)
    return res.url


def wolfram_simple_query(query, app_id):
    base_url = "https://api.wolframalpha.com/v2/result?i={0}&appid={1}"
    query_url = base_url.format(urllib.parse.quote(query), app_id)
    return requests.get(query_url).text


def td_format(td_object):
    ## Straight copy paste from here: https://stackoverflow.com/questions/538666/format-timedelta-to-string
    seconds = int(td_object.total_seconds())
    periods = [
        ("year", 60 * 60 * 24 * 365),
        ("month", 60 * 60 * 24 * 30),
        ("day", 60 * 60 * 24),
        ("hour", 60 * 60),
        ("minute", 60),
        ("second", 1),
    ]

    strings = []
    for period_name, period_seconds in periods:
        if seconds > period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            has_s = "s" if period_value > 1 else ""
            strings.append("%s %s%s" % (period_value, period_name, has_s))

    return ", ".join(strings)


def get_props(obj):
    """Returns properties of the class"""
    return inspect.getmembers(obj, lambda a: not (inspect.isroutine(a)))


def draw_options_table(options):
    table = Texttable()
    table.set_deco(Texttable.VLINES | Texttable.HEADER | Texttable.HLINES)
    table.set_cols_dtype(["a", "a"])  # automatic
    table.set_cols_align(["l", "l"])
    table.add_rows(
        [["name", "value"], *[[name, val] for name, val in options], ]
    )
    return table.draw()


async def success(message):
    await message.add_reaction("✅")


async def failed(message):
    await message.add_reaction("❌")
