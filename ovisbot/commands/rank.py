import discord
import logging
import re
import requests
import ovisbot.locale as i18n

from datetime import datetime
from discord.ext.commands import CommandError

from ovisbot.helpers import chunkify
from ovisbot.db_models import CTF, Challenge, BotConfig

logger = logging.getLogger(__name__)


class NotConfiguredException(CommandError):
    pass


class RankCommandsMixin:
    def load_commands(self):
        """Hooks commands with bot subclass"""
        bot = self

        @bot.group()
        async def rank(ctx):
            """
            Collection of team ranking commands
            """
            if ctx.invoked_subcommand is None:
                subcomms = [sub_command for sub_command in ctx.command.all_commands]
                await ctx.send(
                    "Ranking is not tracked at the moment.\nAvailable rankings are:\n```{0}```".format(
                        " ".join(subcomms)
                    )
                )

        @rank.command(name="htb")
        async def rank_htb(ctx):
            """
            Displays Hack The Box team ranking
            """
            if self.config.HTB_TEAM_ID is None:
                raise NotConfiguredException("Variable HTB_TEAM_ID is not configured")

            headers = {
                "Host": "www.hackthebox.eu",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }
            url = "https://www.hackthebox.eu/teams/profile/{0}".format(
                self.config.HTB_TEAM_ID
            )
            r = requests.get(url, headers=headers)
            result = re.search(
                '<i class="fas fa-user-chart"></i> (.*)</span><br>', r.text
            )

            status_response = i18n._("Position: " + result.group(1))

            embed = discord.Embed(
                title="Hack The Box Team Ranking",
                colour=discord.Colour(0x7ED321),
                url="https://www.hackthebox.eu",
                description=status_response,
                timestamp=datetime.now(),
            )

            embed.set_thumbnail(
                url="https://forum.hackthebox.eu/uploads/RJZMUY81IQLQ.png"
            )
            embed.set_footer(
                text="CYberMouflons",
                icon_url="https://i.ibb.co/yW2mYjq/cybermouflons.png",
            )
            await ctx.channel.send(embed=embed)

        @rank.command(name="ctftime")
        async def rank_ctftime(ctx):
            """
            Displays team ranking on Ctftime.
            """
            if self.config.CTFTIME_TEAM_ID is None:
                raise NotConfiguredException(
                    "Variable CTFTIME_TEAM_ID is not configured"
                )

            url = "https://ctftime.org/api/v1/teams/{0}/".format(
                self.config.CTFTIME_TEAM_ID
            )
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0",
            }
            r = requests.get(url, headers=headers)
            data = r.json()
            status_response = i18n._(
                "Position: "
                + str(data["rating"][0][str(datetime.now().year)]["rating_place"])
            )

            embed = discord.Embed(
                title="CTFTime Ranking",
                colour=discord.Colour(0xFF0035),
                url="https://ctftime.org/",
                description=status_response,
                timestamp=datetime.now(),
            )

            embed.set_thumbnail(
                url="https://pbs.twimg.com/profile_images/2189766987/ctftime-logo-avatar_400x400.png"
            )
            embed.set_footer(
                text="CYberMouflons",
                icon_url="https://i.ibb.co/yW2mYjq/cybermouflons.png",
            )

            await ctx.channel.send(embed=embed)

        @rank_ctftime.error
        async def ranking_error(ctx, error):
            if isinstance(error, NotConfiguredException):
                await ctx.channel.send(
                    i18n._("Configuration missing: {0}".format(error.args[0]))
                )
