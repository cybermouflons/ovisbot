import logging
from ovisbot.helpers import chunkify
import struct
import string
import crypt

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

    @utils.command()
    async def genshadow(self, ctx, cleartext, method=None):
        """
        genshadow, generates a UNIX password hash and a corresponding /etc/shadow entry
        and is intended for usage in boot2root environments

        Available hash types:
            + MD5
            + Blowfish
            + SHA-256
            + SHA-512
        """
        __methods = {
            "1": crypt.METHOD_MD5,
            "MD5": crypt.METHOD_MD5,
            "2": crypt.METHOD_BLOWFISH,
            "BLOWFISH": crypt.METHOD_BLOWFISH,
            "5": crypt.METHOD_SHA256,
            "SHA256": crypt.METHOD_SHA256,
            "6": crypt.METHOD_SHA512,
            "SHA512": crypt.METHOD_SHA512,
        }
        if method and not method.isnumeric():
            method = method.upper()
        method = __methods.get(method, None)

        unix_passwd = crypt.crypt(cleartext, method)
        shadow = f"root:{unix_passwd}:0:0:99999:7::"
        await ctx.send(f"{cleartext}:\n" + f"=> {unix_passwd}\n" + f"=> {shadow}")


def setup(bot):
    bot.add_cog(Utils(bot))
