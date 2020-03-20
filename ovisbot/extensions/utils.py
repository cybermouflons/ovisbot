import logging
import struct

from Crypto.Util.number import long_to_bytes, bytes_to_long
from discord.ext import commands

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def utils(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid command passed.  Use !help.")

    @utils.command()
    async def stol(self, ctx, params):
        await ctx.send(bytes_to_long(params.encode("utf-8")))

    @utils.command()
    async def ltos(self, ctx, params):
        await ctx.send(long_to_bytes(params))


def setup(bot):
    bot.add_cog(Utils(bot))
