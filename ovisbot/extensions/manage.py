import logging

from discord.ext import commands
from ovisbot.db_models import CTF
from ovisbot.config import get_config
from ovisbot.helpers import success

logger = logging.getLogger(__name__)


class Manage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(hidden=True)
    async def manage(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid command passed.  Use !help.")

    @manage.command()
    @commands.has_role("Arxitraoullos")
    async def maintenance(self, ctx):
        config = get_config()
        config.IS_MAINTENANCE = not config.IS_MAINTENANCE
        config.save()
        await success(ctx.message)
        if config.IS_MAINTENANCE:
            await ctx.send("Maintenance mode enabled!")
        else:
            await ctx.send("Maintenance mode disabled!")

    @maintenance.error
    async def maintenance_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRole):
            await ctx.send("Σαν να τζαί εν μου φατσάρεις για Αρχιτράουλλος εσυ...")

    @manage.command()
    @commands.has_permissions(administrator=True)
    async def dropctfs(self, ctx):
        CTF._mongometa.collection.drop()
        await ctx.channel.send("Πάππαλα τα CTFs....")


def setup(bot):
    bot.add_cog(Manage(bot))
