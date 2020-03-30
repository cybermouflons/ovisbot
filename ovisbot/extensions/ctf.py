import datetime
import discord
import logging
import sys
import re
import requests
import dateutil.parser

from discord.ext import commands
from pymodm.errors import ValidationError
from ovisbot.db_models import CTF, Challenge
from ovisbot.exceptions import (
    CTFAlreadyExistsException,
    FewParametersException,
    ChallengeAlreadySolvedException,
    ChallengeInvalidCategory,
    ChallengeExistsException,
    ChallengeDoesNotExistException,
    NotInChallengeChannelException,
    CTFAlreadyFinishedException,
    ChallengeNotSolvedException,
    UserAlreadyInChallengeChannelException,
    CTFSharedCredentialsNotSet,
    CtfimeNameDoesNotMatch,
)
from ovisbot.helpers import chunkify, create_corimd_notebook, escape_md

logger = logging.getLogger(__name__)

CHALLENGE_CATEGORIES = ["crypto", "web", "misc", "pwn", "reverse", "stego", "forensics"]


class Ctf(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _get_channel_ctf(self, ctx):
        channel_name = str(ctx.channel.category)
        return CTF.objects.get({"name": channel_name})

    @commands.group()
    async def ctf(self, ctx):
        self.guild = ctx.guild
        self.gid = ctx.guild.id

        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid command passed.  Use !help.")

    @ctf.command()
    async def status(self, ctx):
        channel_name = str(ctx.channel.category)
        ctf = CTF.objects.get({"name": channel_name})
        summary_chunks = chunkify(ctf.challenge_summary(), 1700)
        for chunk in summary_chunks:
            emb = discord.Embed(description=chunk, colour=4387968)
            await ctx.channel.send(embed=emb)

    @status.error
    async def status_error(self, ctx, error):
        if isinstance(error.original, CTF.DoesNotExist):
            await ctx.channel.send(
                "Έφκαλεν η γλώσσα μου μαλλιά ρε! For this command you have to be in a channel created by !ctf create."
            )

    @ctf.command()
    async def archive(self, ctx, *params):
        ctf_name = "-".join(list(params)).replace("'", "").lower()
        ctf = CTF.objects.get({"name": ctf_name})
        category = discord.utils.get(ctx.guild.categories, name=ctf_name)
        ctfrole = discord.utils.get(ctx.guild.roles, name="Team-" + ctf_name)

        if ctfrole is not None:
            await ctfrole.delete()
        for c in category.channels:
            await c.delete()

        await category.delete()
        ctf.name == "__ARCHIVED__" + ctf.name
        ctf.save()

    @archive.error
    async def archive_error(self, ctx, error):
        if isinstance(error.original, CTF.DoesNotExist):
            await ctx.channel.send(
                "Πε μου εσύ αν θορείς κανένα CTF με έτσι όνομα ... Οι πε μου"
            )
        else:
            logger.error(error)
            await ctx.channel.send("Ουπς. Κάτι επήε λάθος.")

    @ctf.command()
    async def create(self, ctx, *params):
        scat = "-".join(list(params)).replace("'", "").lower()
        category = discord.utils.get(ctx.guild.categories, name=scat)

        if category is not None:
            raise CTFAlreadyExistsException

        user = ctx.message.author
        ctfrole = await self.guild.create_role(name="Team-" + scat, mentionable=True)
        await user.add_roles(ctfrole)
        overwrites = {
            self.guild.get_role(self.gid): discord.PermissionOverwrite(
                read_messages=False
            ),
            self.bot.user: discord.PermissionOverwrite(read_messages=True),
            ctfrole: discord.PermissionOverwrite(read_messages=True),
        }
        category = await self.guild.create_category(name=scat, overwrites=overwrites)
        general_channel = await self.guild.create_text_channel(
            name="general", category=category
        )
        CTF(name=category, created_at=datetime.datetime.now()).save()
        await general_channel.send(f"@here Καλως ορίσατε στο {category} CTF")

    @create.error
    async def create_error(self, ctx, error):
        if isinstance(error.original, CTFAlreadyExistsException):
            await ctx.channel.send(
                "Ρε κουμπάρε! This CTF name already exists! Pick another one"
            )

    @ctf.command(aliases=["addchall"])
    async def addchallenge(self, ctx, *params):
        if len(params) < 2:
            raise FewParametersException

        channel_name = str(ctx.channel.category)
        ctf = CTF.objects.get({"name": channel_name})

        challenge_name = params[0].lower()
        category = params[1].lower()
        if category not in CHALLENGE_CATEGORIES:
            raise ChallengeInvalidCategory

        challenges = [
            c for c in ctf.challenges if c.name == channel_name + "-" + challenge_name
        ]
        if len(challenges) > 0:
            raise ChallengeExistsException

        overwrites = {
            self.guild.get_role(self.gid): discord.PermissionOverwrite(
                read_messages=False
            ),
            self.bot.user: discord.PermissionOverwrite(read_messages=True),
            ctx.message.author: discord.PermissionOverwrite(read_messages=True),
        }
        notebook_url = create_corimd_notebook()
        challenge_channel = await ctx.channel.category.create_text_channel(
            channel_name + "-" + challenge_name, overwrites=overwrites
        )
        new_challenge = Challenge(
            name=challenge_channel.name,
            tags=[category],
            created_at=datetime.datetime.now(),
            attempted_by=[ctx.message.author.name],
            notebook_url=notebook_url,
        )
        ctf.challenges.append(new_challenge)
        ctf.save()
        await ctx.channel.send("Εεεφτασέέέ!")
        await challenge_channel.send("@here Ατε να δούμε δώστου πίεση!")
        notebook_msg = await challenge_channel.send(
            f"Ετο τζαι το δευτερούι σου: {notebook_url}"
        )
        await notebook_msg.pin()

    @addchallenge.error
    async def addchallenge_error(self, ctx, error):
        if isinstance(error.original, FewParametersException):
            await ctx.channel.send(
                "Πεε που σου νέφκω που παεις... !ctf addchallenge takes 2 parameters. !help for more info."
            )
        elif isinstance(error.original, CTF.DoesNotExist):
            await ctx.channel.send(
                "For this command you have to be in a channel created by !ctf create."
            )
        elif isinstance(error.original, ChallengeInvalidCategory):
            await ctx.channel.send(
                "Not valid challenge category provided. !help for more info"
            )
        elif isinstance(error.original, ChallengeExistsException):
            await ctx.channel.send(
                "Να μου γελάσεις ρε κοπελλούι; This challenge already exists!"
            )

    @ctf.command(aliases=["rmchall"])
    async def rmchallenge(self, ctx, *params):
        if len(params) < 1:
            raise FewParametersException

        channel_name = str(ctx.channel.category)
        ctf = CTF.objects.get({"name": channel_name})

        challenge_name = params[0].lower()
        challenges = [
            c for c in ctf.challenges if c.name == channel_name + "-" + challenge_name
        ]
        if len(challenges) == 0:
            raise ChallengeDoesNotExistException

        challenge_channel = discord.utils.get(
            ctx.channel.category.channels, name=channel_name + "-" + challenge_name
        )
        for i, c in enumerate(ctf.challenges):
            if c.name == channel_name + "-" + challenge_name:
                del ctf.challenges[i]
                break
        await challenge_channel.delete()
        ctf.save()

    @rmchallenge.error
    async def rmchallenge_error(self, ctx, error):
        if isinstance(error.original, FewParametersException):
            await ctx.channel.send(
                "Τελος πάντων, εν θα πω τίποτε... !ctf rmchall takes 1 parameter. !help for more info."
            )
        elif isinstance(error.original, CTF.DoesNotExist):
            await ctx.channel.send(
                "For this command you have to be in a channel created by !ctf create."
            )
        elif isinstance(error.original, ChallengeDoesNotExistException):
            await ctx.channel.send(
                "Παρέα μου... εν κουτσιάς... Εν έσιει έτσι challenge!"
            )

    @ctf.command()
    async def notes(self, ctx):
        chall_name = ctx.channel.name
        ctf = CTF.objects.get({"name": ctx.channel.category.name})

        # Find challenge in CTF by name
        challenge = next((c for c in ctf.challenges if c.name == chall_name), None)

        if not challenge:
            raise NotInChallengeChannelException

        if challenge.notebook_url != "":
            await ctx.channel.send(f"Notes: {challenge.notebook_url}")
        else:
            await ctx.channel.send("Εν έσσιει έτσι πράμα δαμέ...Τζίλα το...")

    @notes.error
    async def notes_error(self, ctx, error):
        if isinstance(
            error.original, (NotInChallengeChannelException, CTF.DoesNotExist)
        ):
            await ctx.channel.send(
                "Ρε πελλοβρεμένε! For this command you have to be in a ctf challenge channel created by `!ctf addchallenge`."
            )

    @ctf.command()
    @commands.has_permissions(manage_channels=True, manage_roles=True)
    async def finish(self, ctx, *params):
        if len(params) == 0:
            raise FewParametersException
        ctf_name = "-".join(list(params)).replace("'", "").lower()
        ctf = CTF.objects.get({"name": ctf_name})
        if ctf.finished_at is not None:
            raise CTFAlreadyFinishedException
        ctf.finished_at = datetime.datetime.now()
        ctf.save()
        await ctx.channel.send(
            "Ατε.. Μπράβο κοπέλια τζαι κοπέλλες! Να πνάσουμε τζαι εμείς νακκο!"
        )

    @finish.error
    async def finish_error(self, ctx, error):
        if isinstance(error.original, FewParametersException):
            await ctx.channel.send("This command takes parameters. Use `!help`")
        if isinstance(error.original, CTF.DoesNotExist):
            await ctx.channel.send(
                "Εισαι τζαι εσού χαλασμένος όπως τα διαστημόπλοια του Κίτσιου... There is not such CTF name. Use `!status`"
            )
        if isinstance(error.original, CTFAlreadyFinishedException):
            await ctx.channel.send("This CTF has already finished!")

    @ctf.command()
    async def solve(self, ctx):
        chall_name = ctx.channel.name
        ctf = CTF.objects.get({"name": ctx.channel.category.name})

        # Find challenge in CTF by name
        challenge = next((c for c in ctf.challenges if c.name == chall_name), None)

        if not challenge:
            raise NotInChallengeChannelException
        if challenge.solved_at:
            raise ChallengeAlreadySolvedException(challenge.solved_by)

        challenge.solved_by = [ctx.message.author.name] + [
            m.name for m in ctx.message.mentions
        ]
        challenge.solved_at = datetime.datetime.now()
        ctf.save()

        solvers_str = escape_md(
            ", ".join(
                [ctx.message.author.name] + [m.name for m in ctx.message.mentions]
            )
        )
        await ctx.channel.send(
            "Πελλαμός! {0}! Congrats for solving {1}. Έλα κουφεττούα :candy:".format(
                solvers_str, chall_name
            )
        )
        general_channel = discord.utils.get(
            ctx.channel.category.channels, name="general"
        )
        await general_channel.send(
            f"{solvers_str} solved the {chall_name} challenge! :candy: :candy:"
        )

    @solve.error
    async def solve_error(self, ctx, error):
        if isinstance(
            error.original, (NotInChallengeChannelException, CTF.DoesNotExist)
        ):
            await ctx.channel.send(
                "Ρε πελλοβρεμένε! For this command you have to be in a ctf challenge channel created by `!ctf addchallenge`."
            )
        elif isinstance(error.original, ChallengeAlreadySolvedException):
            await ctx.channel.send(
                f'Άρκησες! This challenge has already been solved by {", ".join(error.original.solved_by)}!'
            )

    @ctf.command()
    async def unsolve(self, ctx):
        chall_name = ctx.channel.name
        ctf = CTF.objects.get({"name": ctx.channel.category.name})

        challenge = next((c for c in ctf.challenges if c.name == chall_name), None)

        if not challenge:
            raise NotInChallengeChannelException
        if not challenge.solved_at:
            raise ChallengeNotSolvedException

        challenge.solved_by = None
        challenge.solved_at = None
        ctf.save()

    @unsolve.error
    async def unsolve_error(self, ctx, error):
        if isinstance(
            error.original, (NotInChallengeChannelException, CTF.DoesNotExist)
        ):
            await ctx.channel.send(
                "Ρε πελλοβρεμένε! For this command you have to be in a ctf challenge channel created by `!ctf addchallenge`."
            )
        elif isinstance(error.original, ChallengeNotSolvedException):
            await ctx.channel.send(f"Ρε κουμπάρε.. αφού ένεν λυμένη η ασκηση.")

    @ctf.command()
    async def join(self, ctx, *params):
        scat = "-".join(list(params)).replace("'", "").lower()
        CTF.objects.get({"name": scat})
        ctfrole = discord.utils.get(self.guild.roles, name="Team-" + scat)
        await ctx.message.author.add_roles(ctfrole)

    @join.error
    async def join_error(self, ctx, error):
        if isinstance(error.original, CTF.DoesNotExist):
            await ctx.channel.send(
                "Εεεε!! Τι κάμνεις? There is no such CTF name. Use `!status`"
            )

    @ctf.command()
    async def leave(self, ctx):
        ctf_name = str(ctx.channel.category)
        ctfrole = discord.utils.get(ctx.guild.roles, name="Team-" + ctf_name)
        await ctx.message.author.remove_roles(ctfrole)

    @ctf.command()
    async def attempt(self, ctx, params):
        ctf_name = str(ctx.channel.category)
        ctf = CTF.objects.get({"name": ctf_name})

        chall_name = params

        if chall_name == "--all":
            for challenge in ctf.challenges:
                if (
                    ctx.message.author.name in challenge.attempted_by
                    or challenge.solved_at
                ):
                    continue
                challenge.attempted_by = challenge.attempted_by + [
                    ctx.message.author.name
                ]
                chall_channel = discord.utils.get(
                    ctx.channel.category.channels, name=challenge.name
                )
                await chall_channel.set_permissions(
                    ctx.message.author, read_messages=True
                )

            ctf.save()
            await ctx.channel.send(f"Άμα είσαι κουνόσσιηλλος...")
        else:
            challenge = next(
                (c for c in ctf.challenges if c.name == ctf_name + "-" + chall_name),
                None,
            )
            if not challenge:
                raise ChallengeDoesNotExistException
            if challenge.solved_at:
                raise ChallengeAlreadySolvedException
            if ctx.message.author.name in challenge.attempted_by:
                raise UserAlreadyInChallengeChannelException

            chall_channel = discord.utils.get(
                ctx.channel.category.channels, name=ctf_name + "-" + chall_name
            )
            await chall_channel.set_permissions(ctx.message.author, read_messages=True)

            # TODO(investigate): ch.attempted_by.append(ctx.message.author.name) mutates all embedded challenges
            challenge.attempted_by = challenge.attempted_by + [ctx.message.author.name]
            ctf.save()
            await ctx.channel.send(
                f'Άτε {ctx.message.author.name} μου! Έβαλα σε τζιαι στη λίστα τζείνων που μάχουνται πάνω στο challenge. [{", ".join(challenge.attempted_by)}]'
            )

    @attempt.error
    async def attempt_error(self, ctx, error):
        if isinstance(error.original, CTF.DoesNotExist):
            await ctx.channel.send(
                "For this command you have to be in a channel created by !ctf create."
            )
        elif isinstance(error.original, ChallengeDoesNotExistException):
            await ctx.channel.send(
                "Μα περιπέζεις μας; There is not such a challenge. Create it using !ctf addchallenge"
            )
        elif isinstance(error.original, ChallengeAlreadySolvedException):
            await ctx.channel.send("Ρε μπρο μου... Ελύσαμε το τουτο το challenge αφού.")
        elif isinstance(error.original, UserAlreadyInChallengeChannelException):
            await ctx.channel.send("Ρε αρφούι μου... Είσαι ήδη μέσα στη λιστούα.")
        else:
            await ctx.channel.send(
                "Εν τα κατάφερα να σε βάλω μέσα στη λιστούα... Σόρρυ."
            )

    @ctf.command()
    async def description(self, ctx, *params):
        channel_name = str(ctx.channel.category)

        if len(params) == 0:
            raise FewParametersException

        ctf = CTF.objects.get({"name": channel_name})
        ctf.description = " ".join(params)
        ctf.save()
        await ctx.channel.send("CTF description set!")

    @description.error
    async def description_error(self, ctx, error):
        if isinstance(error.original, FewParametersException):
            await ctx.channel.send(
                "Πεε που σου νέφκω που παεις... !ctf description takes parameters. !help for more info."
            )
        elif isinstance(error.original, CTF.DoesNotExist):
            await ctx.channel.send(
                "For this command you have to be in a channel created by !ctf create."
            )

    @ctf.command()
    @commands.has_permissions(manage_channels=True, manage_roles=True)
    async def delete(self, ctx, *params):
        scat = "-".join(list(params)).replace("'", "").lower()
        ctf = CTF.objects.get({"name": scat})
        category = discord.utils.get(ctx.guild.categories, name=scat)
        ctfrole = discord.utils.get(ctx.guild.roles, name="Team-" + scat)

        if ctfrole is not None:
            await ctfrole.delete()

        for c in category.channels:
            await c.delete()
        await category.delete()
        ctf.delete()

    @delete.error
    async def delete_error(self, ctx, error):
        if isinstance(error.original, CTF.DoesNotExist):
            await ctx.channel.send(
                "Ρε κουμπάρε! There is not any ongoing CTF with such a name."
            )

    @ctf.command()
    async def setcreds(self, ctx, *params):
        if len(params) < 2:
            raise FewParametersException
        channel_name = str(ctx.channel.category)
        ctf = CTF.objects.get({"name": channel_name})
        ctf.username = params[0]
        ctf.password = params[1]
        if len(params) > 2:
            ctf.url = params[2]
        ctf.save()
        await ctx.channel.send("CTF shared credentials set!")

    @setcreds.error
    async def setcreds_error(self, ctx, error):
        if isinstance(error.original, FewParametersException):
            await ctx.channel.send(
                "Πεε που σου νέφκω που παεις... !ctf setcreds takes 2 or more parameters. !help for more info."
            )
        elif isinstance(error.original, CTF.DoesNotExist):
            await ctx.channel.send(
                "For this command you have to be in a channel created by !ctf create."
            )

    @ctf.command(aliases=[])
    async def startdate(self, ctx, *params):
        ctf = self._get_channel_ctf(ctx)
        if params:
            full_params = " ".join(params)
            startdate = dateutil.parser.parse(full_params)
            ctf.start_date = startdate
            ctf.save()
            await ctx.channel.send("Start date set!")
        else:
            startdate = ctf.start_date
            if startdate is None:
                await ctx.channel.send("Ε αν βάλεις καμιάν ημερομηνία να σου την δείξω τζιόλας...!")
            else:
                await ctx.channel.send("**Start time:** {0}".format(startdate))

    @ctf.command(aliases=[])
    async def enddate(self, ctx, *params):
        ctf = self._get_channel_ctf(ctx)
        if params:
            full_params = " ".join(params)
            enddate = dateutil.parser.parse(full_params)
            ctf.end_date = enddate
            ctf.save()
            await ctx.channel.send("End date set!")
        else:
            enddate = ctf.start_date
            if enddate is None:
                await ctx.channel.send("Ε αν βάλεις καμιάν ημερομηνία να σου την δείξω τζιόλας...!")
            else:
                await ctx.channel.send("**End time:** {0}".format(enddate))

    @enddate.error
    @startdate.error
    async def date_error(self, ctx, error):
        if isinstance(error.original, ValueError):
            await ctx.channel.send(
                "Ρε μα ενόμισες μυρίζουμε τα νύσσια μου? Βάλε ρε κουμπάρε μιά ημερομηνία του χαϊρκού!"
            )
        elif isinstance(error.original, CTF.DoesNotExist):
            await ctx.channel.send(
                "Ατού ο γαβρίλης.. For this command you have to be in a channel created by !ctf create."
            )

    @ctf.command()
    async def showcreds(self, ctx):
        channel_name = str(ctx.channel.category)
        ctf = CTF.objects.get({"name": channel_name})
        if not ctf.username or not ctf.password:
            raise CTFSharedCredentialsNotSet
        emb = discord.Embed(description=ctf.credentials(), colour=4387968)
        await ctx.channel.send(embed=emb)

    @showcreds.error
    async def showcreds_error(self, ctx, error):
        if isinstance(error, CTF.DoesNotExist):
            await ctx.channel.send(
                "For this command you have to be in a channel created by !ctf create."
            )
        elif isinstance(error, CTFSharedCredentialsNotSet):
            await ctx.channel.send("This CTF has no shared credentials set!")

    @ctf.command()
    async def setreminder(self, ctx, param="auto"):
        channel_name = str(ctx.channel.category)
        ctf_obj = CTF.objects.get({"name": channel_name})
        if param == "auto":
            upcoming_url = "https://ctftime.org/api/v1/events/"
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0",
            }

            limit = 5
            data = requests.get(upcoming_url, headers=headers, params=str(limit)).json()
            date_for_reminder = ""
            ctf_found = False
            for ctf in data[:limit]:
                ctf_title = ctf["title"]
                if channel_name in ctf_title.lower():
                    ctf_found = True
                    date_for_reminder = ctf["start"]
                    break

            if not ctf_found:
                raise CtfimeNameDoesNotMatch
        else:
            _, date_for_reminder = dateutil.parser.parse(param), param

        # Save reminder to DB
        ctf_obj.reminder = True
        ctf_obj.date_for_reminder = date_for_reminder
        ctf_obj.save()
        await ctx.channel.send(
            f"Εν να σας θυμίσω τουλάχιστον μισή ώρα πριν αρκέψει το {ctf_title}."
        )

    @setreminder.error
    async def setreminder_error(self, ctx, error):
        if isinstance(error.original, CtfimeNameDoesNotMatch):
            await ctx.channel.send(
                f"Ε κουμπάρε, έτσι CTF εν υπάρχει μα ιντα όνομα εδοκες στο channel; Καμε το μόνος σου τζαι κανεί..."
            )
        elif isinstance(error.original, CTF.DoesNotExist):
            await ctx.channel.send("Μέσα σε CTF channel να το κάμεις τουτο ρε καμμά!")
        elif isinstance(error.original, ValueError):
            await ctx.channel.send(f"Μα ίνταμπου τούτη ημερομηνία που μου έδωκες ολάν?")


def setup(bot):
    bot.add_cog(Ctf(bot))
