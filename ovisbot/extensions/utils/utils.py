import logging
import struct
import string
import crypt

from Crypto.Util.number import long_to_bytes, bytes_to_long
from discord.ext import commands

logger = logging.getLogger(__name__)


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
        await ctx.send(
            "`{0}`".format(joined_params.encode("latin-1").hex())
        )

    @utils.command()
    async def hex2str(self, ctx, param):
        """
        Converts hex to string
        """
        await ctx.send("`{0}`".format(bytearray.fromhex(param).decode()))

    @utils.command()
    async def rotn(self, ctx, shift, *params):
        shift = int(shift)
        msg = ' '.join(params)
        shifted = string.ascii_lowercase[shift:] + string.ascii_lowercase[:shift] +\
                  string.ascii_uppercase[shift:] + string.ascii_uppercase[:shift]
        shifted_tab = str.maketrans(string.ascii_letters, shifted)
        shifted_str = msg.translate(shifted_tab)
        await ctx.send(f"{msg} => {shifted_str}")

    @utils.command()
    async def genshadow(self, ctx, *params):
        argc = len(params)            
        if argc == 1 or argc == 2:
            cleartext = params[0]
            method = None
            if argc == 2:
                method = params[1]
                
            __methods = {
                "1": crypt.METHOD_MD5,
                "MD5": crypt.METHOD_MD5,

                "2": crypt.METHOD_BLOWFISH,
                "BLOWFISH": crypt.METHOD_BLOWFISH,

                "5": crypt.METHOD_SHA256,
                "SHA256": crypt.METHOD_SHA256,

                "6": crypt.METHOD_SHA512,
                "SHA512": crypt.METHOD_SHA512
            }
            if method:
                method = method.upper() if method.isalpha() else method
                method = __methods.get(method.upper(), None)
            
            unix_passwd = crypt.crypt(cleartext, method)
            shadow = f"root:{unix_passwd}:0:0:99999:7::"
            await ctx.send(f"{cleartext}:\n" +\
                        f"=> {unix_passwd}\n" +\
                        f"=> {shadow}")
        else:
            await ctx.send("!utils genshadow <cleartext> [<method]>'")

def setup(bot):
    bot.add_cog(Utils(bot))
