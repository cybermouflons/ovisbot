import logging
import discord

from discord.ext.commands import errors as discorderr
from discord.ext import commands

logger = logging.getLogger(__name__)


class Poll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def poll(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid command passed.  Use `!help {0}`".format(__name__))

    @poll.command()
    async def binary(self, ctx, *params):
        if len(params) != 1:
            await ctx.send("This command expects 1 parameter! See `!help poll`")

        poll_q = params[0]

        embed = discord.Embed(title=poll_q, description="", color=int("00fbf5", 16))
        embed.add_field(
            name="Choices:", value=":thumbsup:\tYES\n\n:thumbsdown:\tNO\n\n"
        )
        msg = await ctx.channel.send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")

    @poll.command()
    async def multichoice(self, ctx, *params):
        if len(params) < 2:
            await ctx.send("This command expects 2 or more parameter! See `!help poll`")

        poll_q = params[0]
        options = params[1:]
        option_symbols = ["🇦", "🇧", "🇨", "🇩", "🇪", "🇫", "🇬", "🇭"]

        if len(options) > len(option_symbols):
            await ctx.send(
                "This commands supports only {0} options".format(len(option_symbols))
            )

        embed = discord.Embed(title=poll_q, description="", color=int("00fbf5", 16))
        options_str = "\n\n".join(
            "{0} \t{1}".format(s, o) for s, o in zip(option_symbols, options)
        )

        embed.add_field(name="Choices:", value=options_str + "\n\n")
        msg = await ctx.channel.send(embed=embed)
        for sym in option_symbols[: len(options)]:
            await msg.add_reaction(sym)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, discorderr.ExpectedClosingQuoteError):
            await ctx.channel.send("Expected closing quote.")


def setup(bot):
    bot.add_cog(Poll(bot))
