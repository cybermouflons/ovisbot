import discord
import requests

import ovisbot.locale as i118n

from discord.ext import commands

from ovisbot.core.models import CTF, Challenge
from ovisbot.helpers import chunkify, wolfram_simple_query


class Base(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def status(self, ctx):
        status_response = ""
        ctfs = sorted([c for c in ctx.guild.categories], key=lambda x: x.created_at)
        for ctf in ctfs:
            try:
                ctf_doc = CTF.objects.get({"name": ctf.name})
            except CTF.DoesNotExist:
                continue

            ctfrole = discord.utils.get(ctx.guild.roles, name="Team-" + ctf.name)
            status_response += ctf_doc.status(len(ctfrole.members))

        if len(status_response) == 0:
            status_response = i118n._("CTF list is empty!")
            await ctx.channel.send(status_response)
            return

        for chunk in chunkify(status_response, 1900):
            emb = discord.Embed(description=chunk, colour=4387968)
            await ctx.channel.send(embed=emb)

    @commands.command()
    async def frappe(self, ctx):
        await ctx.channel.send(i118n._("Frappe on it's way...!"))

    @commands.command()
    async def wolfram(self, ctx, *params):
        query = " ".join(list(params))
        await ctx.channel.send(wolfram_simple_query(query))

    @commands.command()
    async def chucknorris(self, ctx):
        joke_url = "http://api.icndb.com/jokes/random"
        response = requests.get(joke_url)
        data = response.json()
        await ctx.channel.send(data["value"]["joke"])

    @commands.command()
    async def contribute(self, ctx):
        await ctx.channel.send("https://github.com/apogiatzis/KyriosZolo")


def setup(bot):
    bot.add_cog(Base(bot))
