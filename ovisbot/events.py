import logging
import discord
import sys
import ovisbot.locale as i18n

from discord.ext.commands.errors import (
    MissingPermissions,
    CommandNotFound,
    ExpectedClosingQuoteError,
)

from ovisbot import __version__

logger = logging.getLogger(__name__)


def hook_events(bot):
    @bot.event
    async def on_ready():
        logger.info("discordpy: {0}".format(discord.__version__))
        logger.info("<" + bot.user.name + " Online>")
        logger.info("OvisBot v{0}".format(__version__))
        await bot.change_presence(
            activity=discord.Game(name="with your mind! Use !help")
        )

    @bot.event
    async def on_message(message):
        # TODO: URI regex to catch shared links
        if bot.user in message.mentions:
            await message.channel.send(i18n._("What?!"))
        await bot.process_commands(message)

    @bot.event
    async def on_message_edit(before, after):
        threshold = bot.config.COMMAND_CORRECTION_WINDOW
        if (
            after.content != before.content
            and after.edited_at.timestamp() - after.created_at.timestamp() <= threshold
        ):
            await bot.process_commands(after)

    @bot.event
    async def on_member_join(member):
        await member.send(
            i18n._(
                "Hello {0}! Welcome to the server! Send {1}help to see a list of available commands".format(
                    member.name, bot.command_prefix
                )
            )
        )
        announcements = discord.utils.get(
            member.guild.text_channels, name="announcements"
        )
        if announcements is not None:
            await announcements.send(
                    i18n._(f"Welcome {member.name}! Take your time to briefly introduce yourself")
            )
