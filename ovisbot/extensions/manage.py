import logging

from discord.ext import commands
from db_models import CTF

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Manage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def manage(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid command passed.  Use !help.")

    @manage.command()
    @commands.has_permissions(administrator=True)
    async def dropctfs(self, ctx):
        CTF._mongometa.collection.drop()
        await ctx.channel.send("Πάππαλα τα CTFs....")


def setup(bot):
    bot.add_cog(Manage(bot))
