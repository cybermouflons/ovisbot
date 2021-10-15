import logging
import struct
import string
from ovisbot.helpers import chunkify


from Crypto.Util.number import long_to_bytes, bytes_to_long
from discord.ext import commands

logger = logging.getLogger(__name__)


def rotn_helper(offset, text):
    shifted = (
        string.ascii_lowercase[offset:]
        + string.ascii_lowercase[:offset]
        + string.ascii_uppercase[offset:]
        + string.ascii_uppercase[:offset]
    )
    shifted_tab = str.maketrans(string.ascii_letters, shifted)
    return text.translate(shifted_tab)


class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def utils(self, ctx):
        """
        Utility commands for various trivial tasks
        """
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid command passed.  Use !help.")

    @utils.command(aliases=["stol"])
    async def str2long(self, ctx, params):
        """
        Converts string to long
        """
        await ctx.send("`{0}`".format(bytes_to_long(params.encode("utf-8"))))

    @utils.command(aliases=["ltos"])
    async def long2str(self, ctx, params):
        """
        Converts long to string
        """
        await ctx.send("`{0}`".format(long_to_bytes(params)))

    @utils.command()
    async def str2hex(self, ctx, *params):
        """
        Converts string to hex
        """
        joined_params = " ".join(params)
        await ctx.send("`{0}`".format(joined_params.encode("latin-1").hex()))

    @utils.command()
    async def hex2str(self, ctx, param):
        """
        Converts hex to string
        """
        await ctx.send("`{0}`".format(bytearray.fromhex(param).decode()))

    @utils.command()
    async def rotn(self, ctx, shift, *params):
        """
        Returns the ROT-n encoding of a message.
        """
        msg = " ".join(params)
        out = "Original message:\n" + msg
        if shift == "*":
            for s in range(1, 14):
                out += f"\n=[ ROT({s}) ]=\n"
                out += rotn_helper(s, msg)
        else:
            shift = int(shift)
            shifted_str = rotn_helper(shift, msg)

            out += f"\n=[ ROT({shift}) ]=\n"
            out += "Encoded message:\n" + shifted_str

        for chunk in chunkify(out, 1700):
            await ctx.send("".join(["```", chunk, "```"]))


def setup(bot):
    bot.add_cog(Utils(bot))
