"""
core.py
====================================
The core module of my example project
"""

import discord
import logging
import os
import sys
import dateutil.parser
import requests
import traceback
import gettext
import ovisbot.locale as i118n
import re

from datetime import datetime, timezone, timedelta
from discord.ext import commands
from discord.ext.commands.errors import (
    MissingPermissions,
    CommandNotFound,
    ExpectedClosingQuoteError,
)
from discord.ext.commands import Bot

from ovisbot import __version__
from ovisbot.helpers import chunkify, wolfram_simple_query
from ovisbot.db_models import CTF, Challenge, BotConfig
from ovisbot.exceptions import FewParametersException
from ovisbot.config import get_config

COMMAND_PREFIX = "!"

token = os.getenv("DISCORD_BOT_TOKEN")
logger = logging.getLogger(__name__)

# Bot Extensions
extensions = [
    "ctf",
    "manage",
    "utils",
    "ctftime",
    "stats",
    "poll",
    "cryptohack",
    "hackthebox",
]

client = discord.Client()
bot = commands.Bot(command_prefix=COMMAND_PREFIX)
config = get_config()

# Events
@bot.event
async def on_ready():
    logger.info("discordpy: {0}".format(discord.__version__))
    logger.info("<" + bot.user.name + " Online>")
    logger.info(__version__)
    await bot.change_presence(activity=discord.Game(name="with your mind! Use !help"))


@bot.event
async def on_error(event, *args, **kwargs):
    for arg in args:
        if isinstance(arg, Exception):
            raise arg


@bot.event
async def on_command_error(ctx, error):
    if ctx.cog is not None:
        # Errors coming from cogs
        logger.info("Received cog exception: {0}".format(error))
        raise error.original
        return

    if isinstance(error, MissingPermissions):
        # Handle missing permissions
        await ctx.channel.send(i118n._("Permission denied."))
    elif isinstance(error, CommandNotFound):
        await ctx.channel.send(i118n._("Command not found"))
    elif isinstance(error, ExpectedClosingQuoteError):
        await ctx.channel.send(i118n._("Command not found"))
    else:
        await ctx.channel.send(i118n._("Something went wrong..."))
        raise error.original


@bot.event
async def on_message(message):

    if bot.user in message.mentions:
        await message.channel.send(i118n._("What?!"))
    await bot.process_commands(message)


@bot.event
async def on_message_edit(before, after):
    threshold = 30  # time in seconds
    if (
        after.content != before.content
        and after.edited_at.timestamp() - after.created_at.timestamp() <= threshold
    ):
        await bot.process_commands(after)


@bot.event
async def on_member_join(member):
    await member.send(
        i118n._(
            "Hello {0}! Welcome to the server! Send {1}help to see a list of available commands".format(
                member.name, COMMAND_PREFIX
            )
        )
    )
    announcements = discord.utils.get(member.guild.text_channels, name="announcements")
    if announcements is not None:
        await announcements.send(
            (
                i118n._(
                    "Welcome {0}! Take your time to briefly introduce yourself".format(
                        member.name
                    )
                )
            )
        )


@bot.command()
async def status(ctx):
    """
    Shows any ongoing, scheduled, finished CTFs in the server.
    """
    status_response = ""
    ctfs = sorted([c for c in ctx.guild.categories], key=lambda x: x.created_at)
    for ctf in ctfs:
        try:
            ctf_doc = CTF.objects.get({"name": ctf.name})
        except CTF.DoesNotExist:
            continue
            # await ctx.channel.send(f"{ctf.name} was not in the DB")
        ctfrole = discord.utils.get(ctx.guild.roles, name="Team-" + ctf.name)
        status_response += ctf_doc.status(len(ctfrole.members))

    if len(status_response) == 0:
        status_response = i118n._("CTF list is empty!")
        await ctx.channel.send(status_response)
        return

    for chunk in chunkify(status_response, 1900):
        emb = discord.Embed(description=chunk, colour=4387968)
        await ctx.channel.send(embed=emb)


@bot.command()
async def frappe(ctx):
    """
    Orders a cold frappe!
    """
    await ctx.channel.send(i118n._("Frappe on it's way...!"))


@bot.command()
async def wolfram(ctx, query):
    """
    Ask wolfram anything you want
    """
    await ctx.channel.send(wolfram_simple_query(query))


@bot.command()
async def chucknorris(ctx):
    """
    Tells a chunk norris joke
    """
    joke_url = "http://api.icndb.com/jokes/random"
    response = requests.get(joke_url)
    data = response.json()
    await ctx.channel.send(data["value"]["joke"])


@bot.command()
async def contribute(ctx):
    """
    Shows contribute information
    """
    await ctx.channel.send("https://github.com/apogiatzis/KyriosZolo")


@bot.group()
async def rank(ctx):
    """
    Collection of team ranking commands
    """
    if ctx.invoked_subcommand is None:
        subcomms = [sub_command for sub_command in ctx.command.all_commands]
        await ctx.send(
            "Ranking is not tracked at the moment.\nAvailable rankings are:\n```{0}```".format(
                " ".join(subcomms)
            )
        )


@rank.command(name="htb")
async def rank_htb(ctx):
    """
    Displays Hack The Box team ranking
    """
    headers = {
        "Host": "www.hackthebox.eu",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    url = "https://www.hackthebox.eu/teams/profile/353"
    r = requests.get(url, headers=headers)
    result = re.search('<i class="fas fa-user-chart"></i> (.*)</span><br>', r.text)
    status_response = i118n._("HTB Ranking: " + result.group(1))
    await ctx.channel.send(status_response)


@rank.command(name="ctftime")
async def rank_ctftime(ctx):
    """
    Displays team ranking on Ctftime.
    """
    url = "https://ctftime.org/api/v1/teams/81678/"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0",
    }
    r = requests.get(url, headers=headers)
    data = r.json()
    status_response = i118n._(
        "CTFTime Ranking: "
        + str(data["rating"][0][str(datetime.now().year)]["rating_place"])
    )
    await ctx.channel.send(status_response)


def launch():
    sys.path.insert(1, os.path.join(os.getcwd(), "ovisbot", "extensions"))
    for extension in extensions:
        bot.load_extension(extension)
    if token is None:
        raise ValueError(i118n._("DISCORD_BOT_TOKEN variable has not been set!"))
    bot.run(token)

@bot.group()
async def rank(ctx):
    if ctx.invoked_subcommand is None:
        subcomms = [sub_command for sub_command in ctx.command.all_commands]
        await ctx.send(
            "Ranking is not tracked at the moment.\nAvailable rankings are:\n```{0}```".format(
                " ".join(subcomms)
            )
        )

@rank.command(name="htb")
async def rank_htb(ctx):
    headers = {
        'Host': 'www.hackthebox.eu',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }
    url = 'https://www.hackthebox.eu/teams/profile/353'
    r = requests.get(url,headers=headers)
    result = re.search('<i class="fas fa-user-chart"></i> (.*)</span><br>', r.text)
    status_response = i118n._("HTB Ranking: "+ result.group(1))
    await ctx.channel.send(status_response)

@rank.command(name="ctftime")
async def rank_ctftime(ctx):
    url = 'https://ctftime.org/api/v1/teams/81678/'
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0",
    }
    r = requests.get(url,headers=headers)
    data = r.json()
    status_response = i118n._("CTFTime Ranking: " + str(data['rating'][0][str(datetime.now().year)]['rating_place']))
    await ctx.channel.send(status_response) 
