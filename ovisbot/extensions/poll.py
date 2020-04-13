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
        """
        Collection of commands to create polls
        """
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid command passed.  Use `!help {0}`".format(__name__))

    @poll.command()
    async def binary(self, ctx, question):
        """
        Creates a binary poll.
        """
        poll_q = question

        embed = discord.Embed(title=poll_q, description="", color=int("00fbf5", 16))
        embed.add_field(
            name="Choices:", value=":thumbsup:\tYES\n\n:thumbsdown:\tNO\n\n"
        )
        msg = await ctx.channel.send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")

    @poll.command()
    async def multichoice(self, ctx, question, *options):
        """
        Creates a multichoice poll
        """
        poll_q = question
        options = options
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
        if isinstance(error, commands.errors.MissingRequiredArgument):
            self.bot.help_command.context = ctx
            await self.bot.help_command.command_callback(ctx, command=str(ctx.command))

        if isinstance(error, discorderr.ExpectedClosingQuoteError):
            await ctx.channel.send("Expected closing quote.")


def setup(bot):
    bot.add_cog(Poll(bot))
