import discord
import logging
import requests
import ovisbot.locale as i118n

from ovisbot.helpers import chunkify, wolfram_simple_query
from ovisbot.db_models import CTF, Challenge, BotConfig

logger = logging.getLogger(__name__)


class BaseCommandsMixin:
    def load_commands(self):
        """Hooks commands with bot subclass"""
        bot = self

        @bot.command()
        async def ping(ctx):
            """
            Ping.... Pong....
            """
            await ctx.channel.send("pong")

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
            await ctx.channel.send(
                wolfram_simple_query(query, bot.config.WOLFRAM_ALPHA_APP_ID)
            )

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
