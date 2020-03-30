import logging
import struct

from Crypto.Util.number import long_to_bytes, bytes_to_long
from discord.ext import commands

logger = logging.getLogger(__name__)


class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def utils(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid command passed.  Use !help.")

    @utils.command(aliases=["stol"])
    async def str2long(self, ctx, params):
        await ctx.send(bytes_to_long(params.encode("utf-8")))

    @utils.command(aliases=["ltos"])
    async def long2str(self, ctx, params):
        await ctx.send(long_to_bytes(params))

    @utils.command()
    async def str2hex(self, ctx, *params):
        joined_params = " ".join(params)
        await ctx.send(joined_params.encode("latin-1").hex())

    @utils.command()
    async def hex2str(self, ctx, param):
        await ctx.send(bytearray.fromhex(param).decode())


def setup(bot):
    bot.add_cog(Utils(bot))
