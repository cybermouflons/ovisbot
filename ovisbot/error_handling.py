import logging
import sys
import ovisbot.locale as i118n

from discord.ext.commands.errors import (
    CommandNotFound,
    ExpectedClosingQuoteError,
    MissingPermissions,
    MissingRole,
    NoPrivateMessage,
)

logger = logging.getLogger(__name__)


def hook_error_handlers(bot):
    """
    General error handlers for global / command errors
    """

    @bot.event
    async def on_error(event, *args, **kwargs):
        logger.info("ON_ERROR")
        logger.info(sys.exc_info())
        for arg in args:
            if isinstance(arg, Exception):
                raise arg

    @bot.event
    async def on_command_error(ctx, error):
        logger.info("ON_ERROR_COMMAND")
        if ctx.cog is not None:
            # Errors coming from cogs
            logger.info("Received cog exception: {0}".format(error))
            raise error.original

        if isinstance(error, MissingPermissions):
            # Handle missing permissions
            await ctx.channel.send(i118n._("Permission denied."))
        elif isinstance(error, NoPrivateMessage):
            await ctx.channel.send(
                i118n._("This command cannot be used in private messages.")
            )
        elif isinstance(error, MissingRole):
            await ctx.channel.send(
                i118n._("You don't have the required role to run this")
            )
        elif isinstance(error, CommandNotFound):
            await ctx.channel.send(i118n._("Command not found"))
        elif isinstance(error, ExpectedClosingQuoteError):
            await ctx.channel.send(i118n._("Missing a quote?"))
        else:
            # TODO: Send this only if the exception was not handled already... How to check this??
            # await ctx.channel.send(i118n._("Something went wrong..."))
            if hasattr(error, "original"):
                raise error.original
            else:
                raise error
