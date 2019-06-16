import datetime
import discord
import logging
import sys

from db_models import CTF, Challenge
from discord.ext import commands
from pymodm.errors import ValidationError
from exceptions import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHALLENGE_CATEGORIES = ["crypto", "web", "misc", "pwn", "reverse", "stego"]


class Ctf(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def ctf(self, ctx):
        self.guild = ctx.guild
        self.gid = ctx.guild.id

        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid command passed.  Use !help.')

    @ctf.command()
    async def status(self, ctx):
        channel_name = str(ctx.channel.category)
        try:
            ctf = CTF.objects.get({'name': channel_name})
            for chunk in ctf.challenge_summary():
                emb = discord.Embed(
                    description=chunk, colour=4387968)
                await ctx.channel.send(embed=emb)
        except CTF.DoesNotExist:
            await ctx.channel.send('Έφκαλεν η γλώσσα μου μαλλιά ρε! For this command you have to be in a channel created by !ctf create.')

    @ctf.command()
    async def create(self, ctx, *params):
        try:
            scat = '-'.join(list(params)).replace("'", "").lower()
            category = discord.utils.get(ctx.guild.categories, name=scat)

            if category is not None: raise CTFAlreadyExistsException

            user = ctx.message.author
            everyone_role = self.guild.get_role(self.gid)
            ctfrole = await self.guild.create_role(name='Team-'+scat, mentionable=True)
            await user.add_roles(ctfrole)
            overwrites = {
                # Everyone
                self.guild.get_role(self.gid): discord.PermissionOverwrite(read_messages=False),
                self.bot.user: discord.PermissionOverwrite(read_messages=True),
                ctfrole: discord.PermissionOverwrite(read_messages=True)
            }
            category = await self.guild.create_category(name=scat, overwrites=overwrites)
            general_channel = await self.guild.create_text_channel(name='general', category=category)
            CTF(name=category, created_at=datetime.datetime.now()).save()
            await general_channel.send(f'@here Καλως ορίσατε στο {category} CTF')
        except CTFAlreadyExistsException:
            await ctx.channel.send('Ρε κουμπάρε! This CTF name already exists! Pick another one')

    @ctf.command()
    async def addchallenge(self, ctx, *params):
        try:
            if len(params) < 2: raise FewParametersException

            channel_name = str(ctx.channel.category)
            ctf = CTF.objects.get({"name": channel_name})

            challenge_name = params[0].lower()
            category = params[1].lower()
            if category not in CHALLENGE_CATEGORIES: raise ChallengeInvalidCategory

            challenges = [c for c in ctf.challenges if c.name == channel_name+'-'+challenge_name]
            if len(challenges) > 0: raise ChallengeExistsException

            overwrites = {
                self.guild.get_role(self.gid): discord.PermissionOverwrite(read_messages=False),
                self.bot.user: discord.PermissionOverwrite(read_messages=True),
                ctx.message.author: discord.PermissionOverwrite(read_messages=True)
            }
            challenge_channel = await ctx.channel.category.create_text_channel(channel_name + "-" + challenge_name, overwrites=overwrites)
            new_challenge = Challenge(name=challenge_channel.name,
                                    tags=[category],
                                    created_at=datetime.datetime.now(),
                                    attempted_by=[ctx.message.author.name])
            ctf.challenges.append(new_challenge)
            ctf.save()
            await ctx.channel.send('Εεεφτασέέέ!')
            await challenge_channel.send('@here Ατε να δούμε δώστου πίεση!')
        except FewParametersException:
            await ctx.channel.send('Πεε που σου νέφκω που παεις... !ctf addchallenge takes 2 parameters. !help for more info.')
        except CTF.DoesNotExist:
            await ctx.channel.send('For this command you have to be in a channel created by !ctf create.')
        except ChallengeInvalidCategory:
            await ctx.channel.send('Not valid challenge category provided. !help for more info')
        except ChallengeExistsException:
            await ctx.channel.send('Να μου γελάσεις ρε κοπελλούι; This challenge already exists!')
        except Exception as e:
            logger.error(e)
            if ctf.challenges[-1].name == challenge_name: ctf.challenges.pop()
            await ctx.channel.send('Ουπς. Κάτι επήε λάθος.')

    @ctf.command()
    @commands.has_permissions(manage_channels=True, manage_roles=True)
    async def finish(self, ctx, *params):
        try:
            if len(params) == 0: raise FewParametersException
            ctf_name = '-'.join(list(params)).replace("'", "").lower()
            ctf = CTF.objects.get({"name": ctf_name})
            if ctf.finished_at != None: raise CTFAlreadyFinishedException
            ctf.finished_at = datetime.datetime.now()
            ctf.save()
            await ctx.channel.send('Ατε.. Μπράβο κοπέλια τζαι κοπέλλες! Να πνάσουμε τζαι εμείς νακκο!')
        except FewParametersException:
            await ctx.channel.send('This command takes parameters. Use `!help`')
        except CTF.DoesNotExist:
            await ctx.channel.send('Εισαι τζαι εσού χαλασμένος όπως τα διαστημόπλοια του Κίτσιου... There is not such CTF name. Use `!status`')
        except CTFAlreadyFinishedException:
            await ctx.channel.send('This CTF has already finished!')
        except Exception as e:
            logger.error(e)
            await ctx.channel.send('Ουπς. Κάτι επήε λάθος.')

    @ctf.command()
    async def solve(self, ctx):
        try:
            chall_name = ctx.channel.name
            ctf = CTF.objects.get({'name': ctx.channel.category.name})

            # Find challenge in CTF by name
            challenge = next((c for c in ctf.challenges if c.name == chall_name), None)

            if not challenge: raise NotInChallengeChannelException
            if challenge.solved_at: raise ChallengeAlreadySolvedException

            challenge.solved_by = [ctx.message.author.name] + \
                [m.name for m in ctx.message.mentions]
            challenge.solved_at = datetime.datetime.now()
            ctf.save()

            await ctx.channel.send('Πελλαμός! {0}! Congrats for solving {1}. Έλα κουφεττούα :candy:'.format(ctx.message.author.name, chall_name))
            general_channel = discord.utils.get(ctx.channel.category.channels, name="general")
            await general_channel.send(f'{ctx.message.author.name} solved the {chall_name} challenge! :candy: :candy:')
        except (NotInChallengeChannelException, CTF.DoesNotExist):
            await ctx.channel.send('Ρε πελλοβρεμένε! For this command you have to be in a ctf challenge channel created by `!ctf addchallenge`.')
        except ChallengeAlreadySolvedException:
            await ctx.channel.send(f'Άρκησες! This challenge has already been solved by {", ".join(challenge.solved_by)}!')
        except Exception as e:
            logger.error(e)
            await ctx.channel.send('Εσαντανώθηκα. Δοκίμασε ξανά ρε παρέα μου.')

    @ctf.command()
    async def unsolve(self, ctx):
        try:
            chall_name = ctx.channel.name
            ctf = CTF.objects.get({'name': ctx.channel.category.name})

            challenge = next((c for c in ctf.challenges if c.name == chall_name), None)

            if not challenge: raise NotInChallengeChannelException
            if not challenge.solved_at: raise ChallengeNotSolvedException

            challenge.solved_by = None
            challenge.solved_at = None
            ctf.save()
        except (NotInChallengeChannelException, CTF.DoesNotExist):
            await ctx.channel.send('Ρε πελλοβρεμένε! For this command you have to be in a ctf challenge channel created by `!ctf addchallenge`.')
        except ChallengeNotSolvedException:
            await ctx.channel.send(f'Ρε κουμπάρε.. αφού ένεν λυμένη η ασκηση.')
        except Exception as e:
            logger.error(e)
            await ctx.channel.send('Εσαντανώθηκα. Δοκίμασε ξανά ρε τσιάκκο.')

    @ctf.command()
    async def join(self, ctx, *params):
        scat = '-'.join(list(params)).replace("'", "").lower()
        try:
            CTF.objects.get({'name': scat})
            ctfrole = discord.utils.get(self.guild.roles, name='Team-'+scat)
            await ctx.message.author.add_roles(ctfrole)
        except CTF.DoesNotExist:
            await ctx.channel.send('Εεεε!! Τι κάμνεις? There is no such CTF name. Use `!status`')

    @ctf.command()
    async def workon(self, ctx, params):
        await ctx.channel.send('`!ctf workon ` is not supported any more. Use `!ctf attempt` instead')

    @ctf.command()
    async def attempt(self, ctx, params):
        ctf_name = str(ctx.channel.category)
        try:
            ctf = CTF.objects.get({'name': ctf_name})

            chall_name = params

            if chall_name == "--all":
                for challenge in ctf.challenges:
                    if ctx.message.author.name in challenge.attempted_by or challenge.solved_at:
                        continue
                    challenge.attempted_by = challenge.attempted_by + [ctx.message.author.name]
                    chall_channel = discord.utils.get(ctx.channel.category.channels, name=challenge.name)
                    await chall_channel.set_permissions(ctx.message.author, read_messages=True)

                ctf.save()
                await ctx.channel.send(f'Άμα είσαι κουνόσσιηλλος...')
            else:
                challenge = next((c for c in ctf.challenges if c.name == ctf_name+'-'+chall_name), None)
                if not challenge: raise ChallengeDoesNotExistException
                if challenge.solved_at: raise ChallengeAlreadySolvedException
                if ctx.message.author.name in challenge.attempted_by: raise UserAlreadyInChallengeChannelException

                chall_channel = discord.utils.get(
                    ctx.channel.category.channels, name=ctf_name + '-' + chall_name)
                await chall_channel.set_permissions(ctx.message.author, read_messages=True)

                # TODO(investigate): ch.attempted_by.append(ctx.message.author.name) mutates all embedded challenges
                challenge.attempted_by = challenge.attempted_by + [ctx.message.author.name]
                ctf.save()
                await ctx.channel.send(f'Άτε {ctx.message.author.name} μου! Έβαλα σε τζιαι στη λίστα τζείνων που μάχουνται πάνω στο challenge. [{", ".join(challenge.attempted_by)}]')

        except CTF.DoesNotExist:
            await ctx.channel.send('For this command you have to be in a channel created by !ctf create.')
        except ChallengeDoesNotExistException:
            await ctx.channel.send('Μα περιπέζεις μας; There is not such a challenge. Create it using !ctf addchallenge')
        except ChallengeAlreadySolvedException:
            await ctx.channel.send(f'Ρε μπρο μου... Ελύσαμε το τουτο το challenge αφού.')
        except UserAlreadyInChallengeChannelException:
            await ctx.channel.send(f'Ρε αρφούι μου... Είσαι ήδη μέσα στη λιστούα. [{", ".join(challenge.attempted_by)}]')
        except Exception as e:
            logger.error(e)
            await ctx.channel.send(f'Εν τα κατάφερα να σε βάλω μέσα στη λιστούα... Σόρρυ.')

    @ctf.command()
    async def description(self, ctx, *params):
        channel_name = str(ctx.channel.category)
        try:
            if len(params) is 0: raise FewParametersException
            ctf = CTF.objects.get({'name': channel_name})
            ctf.description = ' '.join(params)
            ctf.save()
            await ctx.channel.send('CTF description set!')
        except FewParametersException:
            await ctx.channel.send('Πεε που σου νέφκω που παεις... !ctf description takes parameters. !help for more info.')
        except CTF.DoesNotExist:
            await ctx.channel.send('For this command you have to be in a channel created by !ctf create.')
        except Exception as e:
            logger.error(e)
            ctx.channel.send('Oops. Try setting the description again.')

    @ctf.command()
    @commands.has_permissions(manage_channels=True, manage_roles=True)
    async def delete(self, ctx, *params):
        scat = '-'.join(list(params)).replace("'", "").lower()
        try:
            ctf = CTF.objects.get({'name': scat})
            category = discord.utils.get(ctx.guild.categories, name=scat)
            ctfrole = discord.utils.get(ctx.guild.roles, name='Team-'+scat)
            if ctfrole is not None:
                await ctfrole.delete()
            for c in category.channels:
                await c.delete()
            await category.delete()
            ctf.delete()
        except CTF.DoesNotExist:
            await ctx.channel.send('Ρε κουμπάρε! There is not any ongoing CTF with such a name.')
        except Exception as e:
            logger.error(e)
            ctx.channel.send('Something went wrong!')

    @ctf.command()
    async def setcreds(self, ctx, *params):
        try:
            if len(params) != 2: raise FewParametersException
            channel_name = str(ctx.channel.category)
            ctf = CTF.objects.get({"name": channel_name})
            ctf.username = params[0]
            ctf.password = params[1]
            ctf.save()
            await ctx.channel.send('CTF shared credentials set!')
        except FewParametersException:
            await ctx.channel.send('Πεε που σου νέφκω που παεις... !ctf setcreds takes 2 parameters. !help for more info.')
        except CTF.DoesNotExist:
            await ctx.channel.send('For this command you have to be in a channel created by !ctf create.')
        except Exception as e:
            logger.error(e)
            await ctx.channel.send('Ουπς. Έτα ούλα τζιαμέ...')

    @ctf.command()
    async def showcreds(self, ctx):
        channel_name = str(ctx.channel.category)
        try:
            ctf = CTF.objects.get({"name": channel_name})
            if not ctf.username or not ctf.password: raise CTFSharedCredentialsNotSet
            emb = discord.Embed(description=ctf.credentials(), colour=4387968)
            await ctx.channel.send(embed=emb)
        except CTF.DoesNotExist:
            await ctx.channel.send('For this command you have to be in a channel created by !ctf create.')
        except CTFSharedCredentialsNotSet:
            await ctx.channel.send('This CTF has no shared credentials set!')

def setup(bot):
    bot.add_cog(Ctf(bot))
