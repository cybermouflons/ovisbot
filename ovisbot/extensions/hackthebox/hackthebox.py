import re
import os
import logging
import json
import requests
import discord
import dataclasses
import datetime

from discord.ext import commands

from ovisbot.helpers import success, escape_md
from ovisbot.db_models import HTBUserMapping
from json.decoder import JSONDecodeError
from functools import wraps
from bs4 import BeautifulSoup
from parse import parse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclasses.dataclass
class HTBStats:
    points: int
    user_owns: int
    system_owns: int
    challs_solved: int
    global_rank: int

    @classmethod
    def parse(cls, *args):
        return cls(*list(map(int, args)))


class HTBAPIException(Exception):
    pass


class HTBAPIClient(object):
    """
    HTB API: https://github.com/mxrch/htb_api
    """

    def __init__(self, htb_creds_email, htb_creds_pass):
        self.root_url = "https://www.hackthebox.eu"
        self.authenticated = False
        self.session = requests.Session()
        self.htb_creds_email = htb_creds_email
        self.htb_creds_pass = htb_creds_pass
        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0)"
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
        }

    def handle_errors(func):
        @wraps(func)
        def func_wrapper(inst, *args, **kwargs):
            try:
                return func(inst, *args, **kwargs)
            except JSONDecodeError as e:
                return HTBAPIException(e)

        return func_wrapper

    def authenticated(func):
        @wraps(func)
        def func_wrapper(inst, *args, **kwargs):
            if not inst._check_authenticated():
                inst._login(inst.htb_creds_email, inst.htb_creds_pass)
            return func(inst, *args, **kwargs)

        return func_wrapper

    def get(self, url, headers={}):
        req = requests.get(url, headers=self.headers)
        return json.loads(req.text)

    def _get_points_from_soup(self, soup):
        h2_elems = soup.find_all("h2", class_="no-margins")
        for h2_elem in h2_elems:
            i_elem = h2_elem.find("i", class_="fa-crosshairs")
            if i_elem:
                return i_elem.parent.text

    def _get_system_owns_from_soup(self, soup):
        h2_elems = soup.find_all("h2", class_="no-margins")
        for h2_elem in h2_elems:
            i_elem = h2_elem.find("i", class_="pe-7s-ticket")
            if i_elem:
                return i_elem.parent.text

    def _get_user_owns_from_soup(self, soup):
        h2_elems = soup.find_all("h2", class_="no-margins")
        for h2_elem in h2_elems:
            i_elem = h2_elem.find("i", class_="pe-7s-user")
            if i_elem:
                return i_elem.parent.text

    def _get_rank_from_soup(self, soup):
        elem = soup(text=re.compile(r"is at position.*of the Hall of Fame"))
        return parse(
            "Member {username} is at position {rank} of the Hall of Fame.",
            str(elem[0]).strip(),
        )["rank"]

    def _get_challsolved_from_soup(self, soup):
        elem = soup(text=re.compile(r".*has solved.*challenges"))
        return parse(
            "{username} has solved {challsolved} challenges.", str(elem[0]).strip()
        )["challsolved"]

    def _check_authenticated(self):
        url = f"{self.root_url}/login"
        login = self.session.get(url, headers=self.headers)
        if b"loginForm" in login.content:
            self.authenticated = False
            return False
        self.authenticated = True
        return True

    def _login(self, email, password):
        url = f"{self.root_url}/login"
        page = self.session.get(url, headers=self.headers)
        soup = BeautifulSoup(page.content, "lxml")
        token = soup.find("input", {"name": "_token"}).get("value")
        login_data = {"_token": token, "email": email, "password": password}
        self.session.post(url, data=login_data, headers=self.headers)
        if self._check_authenticated():
            logger.info("HTB authentication successful!")
        else:
            logger.error("HTB authentication failed... Disabling commands...")

    @handle_errors
    def identify_user(self, identifier):
        url = f"{self.root_url}/api/users/identifier/{identifier}/"
        return self.get(url)

    @authenticated
    @handle_errors
    def parse_user_stats(self, user_id):
        url = f"{self.root_url}/home/users/profile/{user_id}"
        headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0)"
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
        }
        page = self.session.get(url, headers=headers)
        soup = BeautifulSoup(page.content, "lxml")
        htb_stats = HTBStats.parse(
            self._get_points_from_soup(soup),
            self._get_user_owns_from_soup(soup),
            self._get_system_owns_from_soup(soup),
            self._get_challsolved_from_soup(soup),
            self._get_rank_from_soup(soup),
        )
        return htb_stats


class HackTheBox(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_client = HTBAPIClient(
            bot.config.HTB_CREDS_EMAIL, bot.config.HTB_CREDS_PASS
        )

    @commands.group()
    async def htb(self, ctx):
        """
        Collection of Hack The Box commands
        """
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid command passed. Use `!help`.")

    @htb.command()
    async def connect(self, ctx, identifier=None):
        """
        Link your Hack The Box account
        """
        if isinstance(ctx.channel, discord.DMChannel):
            if identifier is None:
                msg = (
                    "Εν μου έδωκες account identifier! Πάεννε στο https://www.hackthebox.eu/home/settings"
                    "τζαι πιαστο account identifier που εν κάτω κάτω! Μια ζωη να σας παρατζέλλω δαμέσα!"
                )
                await ctx.send(msg)
            else:
                htb_user = self.api_client.identify_user(identifier)
                try:
                    user_mapping = HTBUserMapping.objects.get(
                        {"discord_user_id": ctx.author.id}
                    )
                    user_mapping.htb_user = htb_user["user_name"]
                    user_mapping.htb_user_id = htb_user["user_id"]
                except HTBUserMapping.DoesNotExist:
                    user_mapping = HTBUserMapping(
                        htb_user=htb_user["user_name"],
                        htb_user_id=htb_user["user_id"],
                        discord_user_id=ctx.author.id,
                    )
                finally:
                    user_mapping.save()
                await ctx.send(f"Linked Hack-The-Box as {htb_user['user_name']}!")
                await success(ctx.message)
                self.api_client.parse_user_stats(htb_user["user_id"])
        else:
            await ctx.channel.send(
                "Να σε κλέψουν τζαι να μεν πάρεις είδηση εσυ ρε... Στείλε DM"
            )

    @htb.command()
    async def disconnect(self, ctx):
        """
        Disconecct your Hack The Box account
        """
        htb_mapping = HTBUserMapping.objects.get({"discord_user_id": ctx.author.id})
        htb_mapping.delete()
        await success(ctx.message)

    @htb.command()
    async def stats(self, ctx, user=None):
        """
        Display your Hack The Box stats or any given user's
        """
        if user is None:
            user_id = ctx.author.id
        else:
            user_id = next((m.id for m in ctx.message.mentions), None)
            if user_id is None:
                return

        htb_mapping = HTBUserMapping.objects.get({"discord_user_id": user_id})
        stats = self.api_client.parse_user_stats(htb_mapping.htb_user_id)

        embed = discord.Embed(
            title=f"{htb_mapping.htb_user}",
            colour=discord.Colour(0x7ED321),
            url=f"https://www.hackthebox.eu/home/users/profile/{htb_mapping.htb_user_id}",
            description=f"Currently at position **{stats.global_rank}** of the Hall of Fame.",
            timestamp=datetime.datetime.now(),
        )

        embed.set_thumbnail(url="https://forum.hackthebox.eu/uploads/RJZMUY81IQLQ.png")
        embed.set_footer(
            text="CYberMouflons", icon_url="https://i.ibb.co/yW2mYjq/cybermouflons.png"
        )

        embed.add_field(name="Points", value=f"{stats.points}", inline=True)
        embed.add_field(name="System Owns", value=f"{stats.system_owns}", inline=True)
        embed.add_field(name="User Owns", value=f"{stats.user_owns}", inline=True)
        embed.add_field(
            name="Challenges Solved", value=f"{stats.challs_solved}", inline=True
        )

        await ctx.send(embed=embed)

    @htb.command()
    async def scoreboard(self, ctx):
        """
        Displays internal Hack The Box scoreboard.
        """
        limit = 10
        mappings = HTBUserMapping.objects.all()
        scores = [
            (
                escape_md(self.bot.get_user(mapping.discord_user_id).name),
                self.api_client.parse_user_stats(mapping.htb_user_id),
            )
            for mapping in mappings
        ][:limit]

        scores = sorted(scores, key=lambda s: s[1].points, reverse=True)
        scoreboard = "\n".join(
            "{0}. **{1}**\t{2}".format(idx + 1, s[0], s[1].points)
            for idx, s in enumerate(scores)
        )
        embed = discord.Embed(
            title="Hack The Box Scoreboard",
            colour=discord.Colour(0x7ED321),
            url="https://www.hackthebox.eu",
            description=scoreboard,
            timestamp=datetime.datetime.now(),
        )

        embed.set_thumbnail(url="https://forum.hackthebox.eu/uploads/RJZMUY81IQLQ.png")
        embed.set_footer(
            text="CYberMouflons", icon_url="https://i.ibb.co/yW2mYjq/cybermouflons.png",
        )

        await ctx.send(embed=embed)

    @scoreboard.error
    @disconnect.error
    @connect.error
    @stats.error
    async def generic_error_handler(self, ctx, error):
        if isinstance(error.original, HTBUserMapping.DoesNotExist):
            await ctx.channel.send(
                "Ρε λεβεντη... εν βρίσκω συνδεδεμένο Hack The Box account! (`!htb connect <identifier>`)"
            )
        elif isinstance(error.original, HTBAPIException):
            await ctx.channel.send("Ούπς... κατι επήε λάθος ρε τσιάκκο!")


def setup(bot):
    bot.add_cog(HackTheBox(bot))
