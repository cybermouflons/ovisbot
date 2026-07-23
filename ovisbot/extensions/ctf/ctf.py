import copy
from functools import partial
import discord
import datetime
import logging
import re
import dateutil.parser
import random
import ovisbot.locale as i18n

from datetime import timedelta
from discord.ext import commands
from ovisbot.db_models import CTF, Challenge
import ovisbot.exceptions
from ovisbot.exceptions import (
    CTFAlreadyExistsException,
    ChallengeAlreadySolvedException,
    ChallengeExistsException,
    ChallengeDoesNotExistException,
    NotInChallengeChannelException,
    NotInCTFChannelException,
    CTFAlreadyFinishedException,
    ChallengeNotSolvedException,
    CTFSharedCredentialsNotSet,
    DateMisconfiguredException,
    MissingStartDateException,
)
from ovisbot.helpers import (
    chunkify,
    create_corimd_notebook,
    escape_md,
    failed,
    success,
    td_format,
)
from discord.ext import tasks
from discord import app_commands
from discord.ext.commands import Context
from typing import Union, cast, Optional
import pymodm

logger = logging.getLogger(__name__)

CHALLENGE_CATEGORIES = [
    "crypto",
    "web",
    "misc",
    "pwn",
    "reverse",
    "stego",
    "forensics",
    "hardware",
    "osint",
    "htb",
]

CHALLENGE_DIFFICULTIES = ["easy", "medium", "hard"]

EMOJI = {"solved": "✅", "unsolved": "⌛"}

CHALLENGE_TAGS = (
    {
        "solved": discord.ForumTag(name="solved", emoji=EMOJI["solved"]),
        "unsolved": discord.ForumTag(name="unsolved", emoji=EMOJI["unsolved"]),
    }
    | {x: discord.ForumTag(name=x) for x in CHALLENGE_CATEGORIES}
    | {x: discord.ForumTag(name=x) for x in CHALLENGE_DIFFICULTIES}
)

# difficulty -> (:emoji:, text)
DIFFICULTY_REWARDS = {
    "none": (":candy:", "κουφεττούα"),
    "easy": (":cookie:", "πισκοττούιν"),
    "medium": (":lollipop:", ["μηλούιν", "πίππιλλο", "γλειφιτζούρι"]),
    "hard": (":icecream:", "παωτόν"),
}

MENTION_REGEX = re.compile(r"<@!?(\d+)>")


def is_ctf_channel(
    channel: Union[discord.abc.GuildChannel, discord.Thread],
) -> bool:
    """
    Checks if the channel is a CTF channel.
    A CTF channel is a category with a name that is not archived and has a "challs" forum channel.
    """
    if not (
        (
            isinstance(channel, discord.ForumChannel)
            or isinstance(channel, discord.TextChannel)
        )
        and channel.category is not None
    ):
        return False

    category = channel.category
    if not discord.utils.get(category.channels, name="challs"):
        return False

    ctf = CTF.objects.get({"name": category.name})
    if not ctf:
        return False

    return True


def in_ctf_channel(interaction: discord.Interaction) -> bool:
    """
    Checks if the command is invoked in a CTF channel.
    """
    if (
        not interaction.channel
        or isinstance(interaction.channel, (discord.DMChannel, discord.GroupChannel))
        or not is_ctf_channel(interaction.channel)
    ):
        raise NotInCTFChannelException
    return True


def in_challenge_thread(interaction: discord.Interaction) -> bool:
    """
    Checks if the command is invoked in a challenge thread.
    """
    return (
        isinstance(interaction.channel, discord.Thread)
        and interaction.channel.parent is not None
        and interaction.channel.parent.name == "challs"
        and is_ctf_channel(interaction.channel.parent)
    )


@app_commands.guild_only()
class Ctf(
    commands.GroupCog,
    group_name="ctf",
    group_description="Collection of commands to manage CTFs",
):
    def __init__(self, bot):
        self.bot = bot
        self.check_reminders.start()

    def _get_channel_ctf(self, interaction: discord.Interaction) -> CTF:
        channel = interaction.channel
        if isinstance(channel, discord.Thread):
            channel = channel.parent
        if channel is None or not isinstance(channel, discord.abc.GuildChannel):
            raise NotInCTFChannelException
        ctf_name = cast(discord.CategoryChannel, channel.category).name
        return CTF.objects.get({"name": ctf_name})

    def _get_ctf_category_channel(
        self,
        ctx: Union[Context, discord.Interaction, discord.TextChannel, discord.Thread],
    ) -> discord.CategoryChannel:
        channel = (
            ctx.channel if isinstance(ctx, (Context, discord.Interaction)) else ctx
        )
        if not isinstance(channel, discord.ForumChannel) and not isinstance(
            channel, discord.TextChannel
        ):
            raise NotInCTFChannelException
        if not channel.category:
            raise NotInCTFChannelException
        return channel.category

    @app_commands.command()
    @app_commands.check(in_ctf_channel)
    async def status(self, interaction: discord.Interaction):
        """
        Returns a list of ongoing challenges in the ctf
        """
        assert interaction.channel is not None

        ctf = self._get_channel_ctf(interaction)
        summary_chunks = chunkify(ctf.challenge_summary(), 1700)
        for chunk in summary_chunks:
            emb = discord.Embed(description=chunk, colour=4387968)
            await interaction.response.send_message(embed=emb)

    @app_commands.command()
    @app_commands.check(in_ctf_channel)
    async def archive(self, ctx, ctf_name: str):
        """
        Archive a CTF to the DB and remove it from discord
        """
        ctf_name = ctf_name.lower()
        ctf = CTF.objects.get({"name": ctf_name})
        category = discord.utils.get(ctx.guild.categories, name=ctf_name)
        ctfrole = discord.utils.get(ctx.guild.roles, name="Team-" + ctf_name)

        if ctfrole is not None:
            await ctfrole.delete()
        for c in category.channels:
            await c.delete()

        await category.delete()
        ctf.name = "__ARCHIVED__" + ctf.name  # bug fix (==)
        ctf.save()
        await success(ctx)

    @app_commands.command()
    @commands.has_permissions(manage_channels=True, manage_roles=True)
    async def create(self, interaction: discord.Interaction, ctf_name: str):
        """
        Creates a new CTF
        """
        await interaction.response.defer()
        logger.info("Creating CTF with name: %s", ctf_name)

        user = cast(discord.Member, interaction.user)
        guild = cast(discord.Guild, interaction.guild)

        scat = ctf_name.lower()
        category = discord.utils.get(guild.categories, name=scat)

        if category is not None:
            raise CTFAlreadyExistsException

        ctfrole = await guild.create_role(name="Team-" + scat, mentionable=True)
        await user.add_roles(ctfrole)
        overwrites = {
            guild.get_role(guild.id): discord.PermissionOverwrite(read_messages=False),
            self.bot.user: discord.PermissionOverwrite(read_messages=True),
            ctfrole: discord.PermissionOverwrite(read_messages=True),
        }
        category = await guild.create_category(name=scat, overwrites=overwrites)
        general_channel = await guild.create_text_channel(
            name="general", category=category
        )

        chall_overwrites = overwrites
        chall_overwrites[ctfrole].send_messages = False
        await guild.create_forum(
            name="challs",
            category=category,
            available_tags=list(CHALLENGE_TAGS.values()),
            overwrites=chall_overwrites,
        )
        CTF(name=category, created_at=datetime.datetime.now(), challenges=[]).save()
        await interaction.followup.send(
            content=f"'Εσιει τζεινούρκο CTF, δώκετε μέσα: {category.name}"
        )
        await general_channel.send(f"@here Καλως ορίσατε στο {category} CTF")

    @app_commands.command()
    @app_commands.choices(
        category=[
            app_commands.Choice(name=cat, value=cat) for cat in CHALLENGE_CATEGORIES
        ],
        difficulty=[
            app_commands.Choice(name=diff, value=diff)
            for diff in CHALLENGE_DIFFICULTIES
        ],
    )
    async def addchallenge(
        self,
        interaction: discord.Interaction,
        challname: str,
        category: app_commands.Choice[str],
        difficulty: Optional[app_commands.Choice[str]],
    ):
        """
        Creates a private channel for a challenge.

        Parameters:
            challname (str): Name of the challenge
            category (str): Name of challenge's category
            difficulty (str): Can be one of ["easy", "medium", "hard"]. Optional.
        """
        ctf = self._get_channel_ctf(interaction)

        challenge_name = challname.lower()

        challenges = [c for c in ctf.challenges if c.name == challenge_name]
        if len(challenges) > 0:
            raise ChallengeExistsException

        notebook_url = create_corimd_notebook()

        # Find challenges forum channel
        category_channels = [
            x
            for x in ctf_channel.channels
            if x.name == "challs" and isinstance(x, discord.ForumChannel)
        ]
        if len(category_channels) != 1:
            raise NotInCTFChannelException

        challenges_forum = category_channels[0]
        chosen_tags = ["unsolved", category.value]
        if difficulty:
            chosen_tags.append(difficulty.value)
        tags = [
            tag for tag in challenges_forum.available_tags if tag.name in chosen_tags
        ]
        challenge_channel, _ = await challenges_forum.create_thread(
            name=f"{EMOJI['unsolved']} - {challenge_name}",
            content="@here Ατε να δούμε δώστου πίεση!",
            applied_tags=tags,
        )

        new_challenge = Challenge(
            name=challenge_name,
            tags=[category.value] + ([difficulty.value] if difficulty else []),
            created_at=datetime.datetime.now(),
            attempted_by=[interaction.user.name],
            notebook_url=notebook_url,
        )
        ctf.challenges.append(new_challenge)
        ctf.save()
        await success(interaction, ephemeral=True)
        notebook_msg = await challenge_channel.send(
            f"Ετο τζαι το δευτερούι σου: {notebook_url}"
        )
        await notebook_msg.pin()

    @app_commands.command()
    @app_commands.check(in_ctf_channel)
    async def rmchallenge(self, interaction: discord.Interaction, challname: str):
        """
        Removes the challenge with the given name.
        """
        await interaction.response.defer()
        ctf = self._get_channel_ctf(interaction)

        challenge_name = challname.lower()
        challenges = [c for c in ctf.challenges if c.name == challenge_name]
        challenges = cast(list[Challenge], challenges)
        if len(challenges) == 0:
            raise ChallengeDoesNotExistException

        challenge_channel_name = (
            EMOJI["solved" if challenges[0].solved_at else "unsolved"]
            + " - "
            + challenge_name
        )
        forum_channel = discord.utils.get(
            self._get_ctf_category_channel(interaction).channels, name="challs"
        )
        if not isinstance(forum_channel, discord.ForumChannel):
            raise NotInCTFChannelException

        challenge_channel = discord.utils.get(
            forum_channel.threads, name=challenge_channel_name
        )
        for i, c in enumerate(ctf.challenges):
            if c.name == challenge_name:
                del ctf.challenges[i]
                break
        await challenge_channel.delete()
        ctf.save()
        await success(interaction)

    @app_commands.command()
    @app_commands.check(in_challenge_thread)
    async def notes(self, interaction: discord.Interaction):
        """
        Shows the notebook url for the particular challenge channel that you are currently in. If this command is run outside of a challenge channel, then ovis gets mad.
        """
        chall_name = get_chall_name(interaction)
        ctf = self._get_channel_ctf(interaction)

        # Find challenge in CTF by name
        challenge = next((c for c in ctf.challenges if c.name == chall_name), None)
        assert challenge is not None
        if challenge.notebook_url != "":
            await interaction.response.send_message(f"Notes: {challenge.notebook_url}")
        else:
            await interaction.response.send_message(
                "Εν έσσιει έτσι πράμα δαμέ...Τζίλα το..."
            )

    @app_commands.command()
    @app_commands.check(in_ctf_channel)
    @commands.has_permissions(manage_channels=True, manage_roles=True)
    async def finish(self, interaction: discord.Interaction, ctf_name: str):
        """
        Marks CTF as finished. (Requires manage channels permissions)
        """
        ctf = CTF.objects.get({"name": ctf_name.lower()})
        if ctf.finished_at is not None:
            raise CTFAlreadyFinishedException
        ctf.finished_at = datetime.datetime.now()
        ctf.save()
        await interaction.response.send_message(
            "Ατε.. Μπράβο κοπέλια τζαι κοπέλλες! Να πνάσουμε τζαι εμείς νακκο!"
        )

    @app_commands.command()
    @app_commands.check(in_challenge_thread)
    async def solve(
        self,
        interaction: discord.Interaction,
        solvers: Optional[str],
    ):
        """
        Marks the current challenge as solved by you.

        Arguments:
            solvers (str): A string with mentions of the users that helped you solve the challenge.
        """
        chall_name = get_chall_name(interaction)
        chall_thread = cast(discord.Thread, interaction.channel)
        chall_forum = cast(discord.ForumChannel, chall_thread.parent)
        ctf_category = cast(
            discord.CategoryChannel,
            chall_forum.category,
        )
        ctf = self._get_channel_ctf(interaction)

        # Find challenge in CTF by name
        challenge = next((c for c in ctf.challenges if c.name == chall_name), None)

        if not challenge:
            raise NotInChallengeChannelException
        if challenge.solved_at:
            raise ChallengeAlreadySolvedException(challenge.solved_by)

        # Parse solvers from argument string
        solvers = solvers if solvers else ""
        solvers_user_ids = MENTION_REGEX.findall(solvers)
        users: list[discord.Member] = []

        guild = cast(discord.Guild, interaction.guild)
        for user_id in solvers_user_ids:
            user = guild.get_member(int(user_id))
            if user is None:
                continue
            users.append(user)

        solvers_list = [interaction.user.name] + [user.name for user in users]
        challenge.solved_by = solvers_list
        challenge.solved_at = datetime.datetime.now()
        ctf.save()

        solvers_str = escape_md(", ".join(solvers_list))

        # look for difficulty in challenge's tags
        # default to "none" if no matching difficulty is found
        difficulty = "none"
        tags_lower = [x.lower() for x in challenge.tags]
        for d in DIFFICULTY_REWARDS:
            if d.lower() in tags_lower:
                difficulty = d

        reward = DIFFICULTY_REWARDS[difficulty]
        reward_emoji, reward_text = reward
        if isinstance(reward_text, list):
            reward_text = random.choice(reward_text)

        new_tags = change_tags(chall_thread, add=["solved"], remove=["unsolved"])
        await chall_thread.edit(
            name=f"{EMOJI['solved']} - {chall_name}", applied_tags=new_tags
        )

        await interaction.response.send_message(
            "Πελλαμός! {0}! Congrats for solving {1}. Έλα {2} {3}".format(
                solvers_str, chall_name, reward_text, reward_emoji
            )
        )
        logger.info(f"Looking for #general in {ctf_category.channels}")
        general_channel = discord.utils.get(ctf_category.channels, name="general")
        if not isinstance(general_channel, discord.TextChannel):
            raise NotInCTFChannelException
        await general_channel.send(
            f"{solvers_str} solved the {chall_name} challenge! {reward_emoji} {reward_emoji}"
        )

    @app_commands.command()
    async def unsolve(self, interaction: discord.Interaction):
        """
        Marks the current challenge as unsolved. Allows to to rollback accidental solves.
        """
        chall_name = get_chall_name(interaction)
        chall_thread = cast(discord.Thread, interaction.channel)
        ctf = self._get_channel_ctf(interaction)

        challenge = next((c for c in ctf.challenges if c.name == chall_name), None)

        if not challenge:
            raise NotInChallengeChannelException
        if not challenge.solved_at:
            raise ChallengeNotSolvedException

        new_tags = change_tags(chall_thread, add=["unsolved"], remove=["solved"])
        await chall_thread.edit(
            name=f"{EMOJI['unsolved']} - {chall_name}", applied_tags=new_tags
        )

        challenge.solved_by = None
        challenge.solved_at = None
        ctf.save()
        await success(interaction)

    @app_commands.command()
    async def join(self, interaction: discord.Interaction, ctf_name: str):
        """
        Join an ongoing ctf. Use `status` to see available CTFs.
        """
        scat = "-".join(ctf_name).replace("'", "").lower()
        CTF.objects.get({"name": scat})
        guild = cast(discord.Guild, interaction.guild)
        ctfrole = discord.utils.get(guild.roles, name="Team-" + scat)
        if ctfrole is None:
            raise CTF.DoesNotExist
        user = cast(discord.Member, interaction.user)
        await user.add_roles(ctfrole)
        await success(interaction)

    @app_commands.command()
    @app_commands.check(in_ctf_channel)
    async def leave(self, interaction: discord.Interaction):
        """
        Leave the current CTF.
        """
        ctf_name = self._get_ctf_category_channel(interaction).name
        guild = cast(discord.Guild, interaction.guild)
        ctfrole = discord.utils.get(guild.roles, name="Team-" + ctf_name)
        ctfrole = cast(discord.Role, ctfrole)
        user = cast(discord.Member, interaction.user)
        await user.remove_roles(ctfrole)
        await success(interaction, ephemeral=True)

    @app_commands.command()
    @commands.has_permissions(manage_channels=True, manage_roles=True)
    async def delete(self, interaction: discord.Interaction, ctfname: str):
        """
        Delete a CTF category with all its channel and its user role.
        """
        scat = ctfname.replace("'", "").lower()
        ctf = CTF.objects.get({"name": scat})
        guild = cast(discord.Guild, interaction.guild)
        category = discord.utils.get(guild.categories, name=scat)
        if category is None:
            raise CTF.DoesNotExist
        ctfrole = discord.utils.get(guild.roles, name="Team-" + scat)

        if ctfrole is not None:
            await ctfrole.delete()

        for c in category.channels:
            await c.delete()
        await category.delete()
        ctf.delete()
        await success(interaction)

    @app_commands.command()
    @app_commands.check(in_ctf_channel)
    async def setcreds(
        self,
        interaction: discord.Interaction,
        username: str,
        password: str,
        link: Optional[str] = None,
    ):
        """
        Sets shared credentials to be used by the team members to login to the CTF. Link is the login/home page of the CTF
        """
        ctf = self._get_channel_ctf(interaction)
        ctf.username = username
        ctf.password = password
        if link:
            logger.info(link)
            ctf.url = link
        ctf.save()
        await success(interaction)

        if not (ctf.username and ctf.password):
            raise CTFSharedCredentialsNotSet
        emb = discord.Embed(description=ctf.credentials(), colour=4387968)
        ctf_channel = cast(discord.TextChannel, interaction.channel)
        msg = await ctf_channel.send(embed=emb)
        await msg.pin()
        await success(interaction, ephemeral=True)

    @setcreds.error
    async def setcreds_error(self, interaction: discord.Interaction, error):
        if isinstance(error.original, pymodm.errors.ValidationError):
            await interaction.response.send_message(
                "Βάλε κανένα URL του χαϊρκού!", ephemeral=True
            )

    @app_commands.command()
    @app_commands.check(in_ctf_channel)
    async def startdate(
        self, interaction: discord.Interaction, date: Optional[str] = None
    ):
        """
        Sets the start date of the CTF
        """
        ctf = self._get_channel_ctf(interaction)
        if date:
            startdate = dateutil.parser.parse(date)
            if ctf.end_date and startdate >= ctf.end_date:
                raise DateMisconfiguredException

            ctf.start_date = startdate
            ctf.pending_reminders = []
            ctf.save()
            await success(interaction)
        else:
            startdate = ctf.start_date
            if startdate is None:
                await interaction.response.send_message(
                    "Ε αν βάλεις καμιάν ημερομηνία να σου την δείξω τζιόλας...!",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    "**Start time:** {0}".format(startdate)
                )

    @app_commands.command()
    @app_commands.check(in_ctf_channel)
    async def enddate(
        self, interaction: discord.Interaction, date: Optional[str] = None
    ):
        """
        Sets the end date of the CTF
        """
        ctf = self._get_channel_ctf(interaction)
        if date:
            enddate = dateutil.parser.parse(date)

            if ctf.start_date and enddate <= ctf.start_date:
                raise DateMisconfiguredException

            ctf.end_date = enddate
            ctf.save()
            await success(interaction)
        else:
            enddate = ctf.end_date
            if enddate is None:
                await interaction.response.send_message(
                    "Ε αν βάλεις καμιάν ημερομηνία να σου την δείξω τζιόλας...!",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    "**End time:** {0}".format(enddate)
                )

    @enddate.error
    @startdate.error
    async def date_error(self, interaction: discord.Interaction, error):
        if isinstance(error.original, ValueError):
            await interaction.response.send_message(
                "Ρε μα ενόμισες μυρίζουμε τα νύσσια μου? Βάλε ρε κουμπάρε μιά ημερομηνία του χαϊρκού!",
                ephemeral=True,
            )

    @app_commands.command()
    @app_commands.check(in_ctf_channel)
    async def showcreds(self, interaction: discord.Interaction):
        """
        Displays shared credentials for the team
        """
        ctf = self._get_channel_ctf(interaction)
        if not (ctf.username and ctf.password):
            raise CTFSharedCredentialsNotSet
        emb = discord.Embed(description=ctf.credentials(), colour=4387968)
        await interaction.response.send_message(embed=emb)

    reminders = app_commands.Group(
        name="reminders", description="Manage reminders for the CTF"
    )

    @reminders.command()
    async def list(self, interaction: discord.Interaction):
        """
        Displays existing reminders.
        """
        ctf = self._get_channel_ctf(interaction)
        if ctf.pending_reminders:
            await interaction.response.send_message(
                "\n".join(
                    "**{0})** {1}".format(idx + 1, r)
                    for idx, r in enumerate(ctf.pending_reminders)
                )
            )
        else:
            await interaction.response.send_message(
                "Εν έσσιει κανένα reminder ρε τσιάκκο... Εν να βάλεις όξα?",
                ephemeral=True,
            )

    @app_commands.command(name="countdown")
    @app_commands.check(in_ctf_channel)
    async def countdown(self, interaction: discord.Interaction):
        """
        Displays countdown until CTF starts. Requires a start date to be set.
        @raises MissingStartDateException if ctf.start_date is None
        """
        ctf = self._get_channel_ctf(interaction)

        if not ctf.start_date:
            raise MissingStartDateException

        now = datetime.datetime.now()
        if now < ctf.start_date:
            await interaction.response.send_message(
                "⏰   **" + td_format(ctf.start_date - now) + "** to start"
            )
        else:
            if ctf.end_date is None:
                await interaction.response.send_message(
                    "Ρε παίχτη μου αρκεψεν... ξύπνα!"
                )
            elif now < ctf.end_date:
                await interaction.response.send_message(
                    "⏰   **" + td_format(ctf.end_date - now) + "** to finish"
                )
            else:
                await interaction.response.send_message(
                    "Ρε παίχτη μου ετέλειωσεν... ξύπνα!"
                )

    @reminders.command(name="add")
    async def reminders_add(
        self, interaction: discord.Interaction, unit: str, amount: int
    ):
        """
        Adds a new reminder. Unit can be any time unit (hours, minutes, days...)
        Negative amount parameters means adda reminder before the ctf starts.
        """
        ctf = self._get_channel_ctf(interaction)

        if not ctf.start_date:
            raise MissingStartDateException

        amount = int(amount)
        # unit = unit
        # ?? unnesecary assignment to self
        td = timedelta(**{unit: amount})

        reminder_date = ctf.start_date + td
        ctf.pending_reminders.append(reminder_date)
        ctf.save()

        await success(interaction)

    @reminders_add.error
    @countdown.error
    async def reminders_add_error(self, interaction: discord.Interaction, error):
        if isinstance(error.original, (ValueError, TypeError)):
            await interaction.response.send_message(
                "Εν να σε αφήκω να καταλάβεις μόνος σου τι μαλακία έκαμες..."
            )

    @reminders.command(name="rm")
    async def reminders_rm(self, interaction: discord.Interaction, reminder_idx: int):
        """
        Removes a reminder from the reminder list.
        """
        ctf = self._get_channel_ctf(interaction)
        del ctf.pending_reminders[int(reminder_idx) - 1]
        ctf.save()
        await interaction.response.send_message("Reminder list updated!")

    @reminders_rm.error
    async def reminders_rm_error(self, interaction: discord.Interaction, error):
        if isinstance(error.original, IndexError):
            await interaction.response.send_message(
                "Εν να σε αφήκω να καταλάβεις μόνος σου τι μαλακία έκαμες..."
            )
        elif isinstance(error.original, ValueError):
            await interaction.response.send_message("Index μανα μου ... Index!")

    # @app_commands.command()
    # async def reminders(self, ctx, param="auto"):
    #     ctf_obj = self._get_channel_ctf(ctx)
    # if param == "auto":
    #     upcoming_url = "https://ctftime.org/api/v1/events/"
    #     headers = {
    #         "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0",
    #     }
    #     limit = 5
    #     data = requests.get(upcoming_url, headers=headers, params=str(limit)).json()
    #     date_for_reminder = ""
    #     ctf_found = False
    #     for ctf in data[:limit]:
    #         ctf_title = ctf["title"]
    #         if channel_name in ctf_title.lower():
    #             ctf_found = True
    #             date_for_reminder = ctf["start"]
    #             break

    #     if not ctf_found:
    #         raise CtfimeNameDoesNotMatch
    # else:
    #     _, date_for_reminder = dateutil.parser.parse(param), param

    # Save reminder to DB

    # ctf_obj.reminder = True
    # ctf_obj.date_for_reminder = date_for_reminder
    # ctf_obj.save()
    # await ctx.channel.send(
    #     f"Εν να σας θυμίσω τουλάχιστον μισή ώρα πριν αρκέψει το {ctf_title}."
    # )

    @tasks.loop(seconds=60)
    async def check_reminders(self):
        if len(self.bot.guilds) == 0:
            return
        REMINDERS_CHANNEL_ID = 579049835064197157
        guild = self.bot.guilds[0]
        reminders_channel = guild.get_channel(REMINDERS_CHANNEL_ID)
        ctfs = [c for c in guild.categories]
        for ctf in ctfs:
            try:
                ctf_doc = CTF.objects.get({"name": ctf.name})
                now = datetime.datetime.now()

                # Check Custom Reminders
                if ctf_doc.start_date and ctf_doc.pending_reminders:
                    for reminder in copy.deepcopy(ctf_doc.pending_reminders):
                        if now >= reminder:
                            logger.info(
                                "Sending reminder to {0}".format(reminders_channel)
                            )
                            delta = abs(ctf_doc.start_date - now)
                            if now > ctf_doc.start_date:
                                reminder_text = "⏰ Ατέ ρε αχαμάκκιες... Εν να μπείτε? Το **{0}** άρκεψε εσσιει τζαί **{1}** λεπτά! ⏰"
                            else:
                                reminder_text = "⏰  Ντριιιινγκ... Ντριιινγκ!! Ατέ μανα μου, ξυπνάτε! Το **{0}** ξεκινά σε **{1}** λεπτά! ⏰"
                            await reminders_channel.send(
                                reminder_text.format(ctf.name, int(delta.seconds / 60))
                            )
                            ctf_doc.pending_reminders.remove(reminder)
                            ctf_doc.save()

                # Check Start Reminders
                now_truncated = now.replace(second=0, microsecond=0)
                if (
                    ctf_doc.start_date
                    and ctf_doc.start_date.replace(second=0, microsecond=0)
                    == now_truncated
                ):
                    await reminders_channel.send(
                        "⛳ Το **{0}** άρκεψεν! Ταράσσετε εμπάτε! @here".format(
                            ctf_doc.name
                        )
                    )

                # Check End Reminders
                now_truncated = now.replace(second=0, microsecond=0)
                if (
                    ctf_doc.end_date
                    and ctf_doc.end_date.replace(second=0, microsecond=0)
                    == now_truncated
                ):
                    await reminders_channel.send(
                        "⛳ Πάππαλλα το **{0}**! Τέλος! Εεε? Εδέραμε? @here ".format(
                            ctf_doc.name
                        )
                    )
            except CTF.DoesNotExist:
                continue

    async def cog_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        logger.info("Error in CTF cog: %s", error)
        respond = partial(interaction.response.send_message, ephemeral=True)
        for exc_type in ovisbot.exceptions.OvisBotException.__subclasses__():
            if isinstance(error.original, exc_type):
                await respond(error.original.message)
                break
        else:
            if isinstance(error.original, CTF.DoesNotExist):
                await respond(
                    "Εισαι τζαι εσού χαλασμένος όπως τα διαστημόπλοια του Κίτσιου... There is no such CTF name. Use `!status`"
                )
            else:
                logger.error("Error in CTF cog: %s", error)
                await respond("Ουπς. Κάτι επήε λάθος.")


def change_tags(thread: discord.Thread, add: list[str] = [], remove: list[str] = []):
    new_tags = thread.applied_tags
    for t in new_tags:
        if t.name in remove:
            new_tags.remove(t)
    forum_channel = thread.parent
    if not isinstance(forum_channel, discord.ForumChannel):
        raise NotInChallengeChannelException
    new_tags += [x for x in forum_channel.available_tags if x.name in add]
    return new_tags


def get_chall_name(ctx: Union[Context, discord.Interaction]) -> str:
    channel = ctx.channel
    if not isinstance(channel, discord.Thread):
        raise NotInChallengeChannelException
    name = channel.name
    for emoji in EMOJI.values():
        if name.startswith(emoji + " - "):
            return name[len(emoji + " - ") :]
    return name


async def setup(bot):
    await bot.add_cog(Ctf(bot))
