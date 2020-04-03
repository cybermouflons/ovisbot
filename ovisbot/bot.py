import discord
import logging

import ovisbot.locale as i118n

from discord.ext.commands import Bot
from discord.ext.commands.errors import (
    CommandNotFound,
    ExpectedClosingQuoteError,
    MissingPermissions,
)

from ovisbot import __version__

logger = logging.getLogger(__name__)


class OvisBot(Bot):
    def __init__(self, *args, loop=None, **kwargs):
        super().__init__(*args, loop=loop, **kwargs)

    async def on_ready(self):
        logger.info("discordpy: {0}".format(discord.__version__))
        logger.info("<" + self.user.name + " Online>")
        logger.info(__version__)
        await self.change_presence(
            activity=discord.Game(name="with your mind! Use !help")
        )

    async def on_error(self, event, *args, **kwargs):
        for arg in args:
            if isinstance(arg, Exception):
                raise arg

    async def on_message(self, message):
        if self.user in message.mentions:
            await message.channel.send(i118n._("What?!"))
        await self.process_commands(message)

    async def on_message_edit(self, before, after):
        threshold = 30  # time in seconds
        if (
            after.content != before.content
            and after.edited_at.timestamp() - after.created_at.timestamp() <= threshold
        ):
            await self.process_commands(after)

    async def on_command_error(self, ctx, error):
        if ctx.cog is not None:
            # Errors coming from cogs
            logger.info("Received cog exception: {0}".format(error))
            raise error.original
            return

        if isinstance(error, MissingPermissions):
            # Handle missing permissions
            await ctx.channel.send(i118n._("Permission denied."))
        elif isinstance(error, CommandNotFound):
            await ctx.channel.send(i118n._("Command not found"))
        elif isinstance(error, ExpectedClosingQuoteError):
            await ctx.channel.send(i118n._("Command not found"))
        else:
            await ctx.channel.send(i118n._("Something went wrong..."))
            raise error.origina

    async def on_member_join(self, member):
        await member.send(
            i118n._(
                "Hello {0}! Welcome to the server! Send {1}help to see a list of available commands".format(
                    member.name, self.command_prefix
                )
            )
        )
        announcements = discord.utils.get(
            member.guild.text_channels, name="announcements"
        )
        if announcements is not None:
            await announcements.send(
                (
                    i118n._(
                        "Welcome {0}! Take your time to briefly introduce yourself".format(
                            member.name
                        )
                    )
                )
            )
