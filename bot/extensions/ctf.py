import datetime
import discord
import logging
import sys

from discord.ext import commands
from db_models import CTF, Challenge
from pymodm.errors import ValidationError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))

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
<<<<<<< HEAD
        channel_name = str(ctx.channel.category)
        try:
            ctf = CTF.objects.get({'name': channel_name})
        except CTF.DoesNotExist:
            await ctx.channel.send('Έφκαλεν η γλώσσα μου μαλλιά ρε! For this command you have to be in a channel created by !ctf create.')
            return
        emb = discord.Embed(
            description=ctf.challenge_summary(), colour=4387968)
        await ctx.channel.send(embed=emb)
=======
        channelname = str(ctx.channel.category)
        if serverdb.ctfs.find({"channelname": channelname}).count() > 0:
            status_response = """
            =================== {0} ===================
            """.format(channelname)
            ctf_doc = serverdb.ctfs.find_one({"channelname": channelname})
            solved_response, unsolved_response = "> Solved\n", "> Unsolved\n"
            for challenge in ctf_doc['challenges']:
                if challenge['solved']:
                    solved_response += ":sparkles: **{0}** ({1}) (Solved by: {2})\n".format(challenge['name'],
                                                                                          challenge['category'],
                                                                                          challenge['solved_by'])
                else:
                    active_members = discord.utils.get(ctx.channel.category.channels, name=channelname+'-'+challenge['name']).members
                    active_members = [m for m in active_members if m.bot == False]
                    unsolved_response += "[{0} active] **{1}** ({2}): {3}\n".format(len(active_members),
                                                                              challenge['name'],
                                                                              challenge['category'],
                                                                              ', '.join([m.name for m in active_members]))
            status_response += solved_response
            status_response += unsolved_response
            while len(status_response) > 2000: # Embed has a limit of 2048 chars
                idx = status_response.index('\n',2000)
                emb = discord.Embed(description=status_response[:idx], colour=4387968)
                await ctx.channel.send(embed=emb)
                status_response = status_response[idx:]
            emb = discord.Embed(description=status_response, colour=4387968)
            await ctx.channel.send(embed=emb)
        else:
            await ctx.channel.send('Έφκαλεν η γλώσσα μου μαλιά ρε! For this command you have to be in a channel created by !ctf create.')
>>>>>>> master

    @ctf.command()
    async def create(self, ctx, *params):
        scat = '-'.join(list(params)).replace("'", "").lower()
        category = discord.utils.get(ctx.guild.categories, name=scat)
        # Check if category exists. Create it if it doesn't.
        if category is not None:
            await ctx.channel.send('Ρε κουμπάρε! This CTF name already exists! Pick another one')
            return

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
        # TODO: Manage permissions  overwrites={everyone_role: discord.Permissions.none (), ctfrole:523328
        category = await self.guild.create_category(name=scat, overwrites=overwrites)
        await self.guild.create_text_channel(name='general', category=category)
<<<<<<< HEAD
        CTF(name=scat, created_at=datetime.datetime.now()).save()

    @ctf.command()
    async def addchallenge(self, ctx, *params):
        if len(params) < 2:
            await ctx.channel.send('Πεε που σου νέφκω που παεις... !ctf addchallenge takes 2 parameters. !help for more info.')
            return

        channel_name = str(ctx.channel.category)
        try:
            ctf = CTF.objects.get({"name": channel_name})
        except CTF.DoesNotExist:
=======
        serverdb.ctfs.insert_one({"channelname":scat, 
                                  "active": True,
                                  "created_at": datetime.datetime.now(),
                                  "challenges": []})
    
    @ctf.command()
    @commands.has_permissions(manage_channels=True, manage_roles=True)
    async def finish(self, ctx, *params):
        if len(params) > 0:
            ctf_name = '-'.join(list(params)).replace("'", "").lower()
            ctf_doc = serverdb.ctfs.find_one({"channelname": ctf_name})
            if ctf_doc != None:
                if ctf_doc['active']:
                    serverdb.ctfs.update_one({"channelname": ctf_name},
                                            {"$set": { "active": False}})
                    await ctx.channel.send('Ατε.. Μπράβο κοπέλια τζαι κοπέλλες! Να πνάσουμε τζαι εμείς νακκο!')
                else:
                    await ctx.channel.send('This CTF has already finished!')
            else:
                await ctx.channel.send('Εισαι τζαι εσού χαλασμένος όπως τα διαστημόπλοια του Κίτσιου... There is not such CTF name. Use `!status`')
        else:
            await ctx.channel.send('This command takes parameters. Use `!help`')
    
    @ctf.command()
    async def addchallenge(self, ctx, *params):
        # TODO: I don't like nested ifs for validation... Change them to try catch pattern with exceptions
        channelname = str(ctx.channel.category)
        if serverdb.ctfs.find({"channelname": channelname}).count() > 0:
            if (len(params) == 2):
                chall_name = params[0].lower()
                category = params[1]
                if category in CHALLENGE_CATEGORIES:
                    chall_channel = discord.utils.get(ctx.channel.category.channels, name=channelname + '-' + chall_name)
                    if chall_channel == None:
                        overwrites = {
                            self.guild.get_role(self.gid): discord.PermissionOverwrite(read_messages=False),
                            self.bot.user: discord.PermissionOverwrite(read_messages=True),
                            ctx.message.author: discord.PermissionOverwrite(read_messages=True)
                        }
                        ch = await ctx.channel.category.create_text_channel(channelname + "-" + chall_name, overwrites=overwrites)
                        serverdb.ctfs.update_one({"channelname": channelname},
                                                 {"$push": {'challenges':{'name': ch.name[len(channelname)+1:],
                                                                          'solved': False,
                                                                          'category': category}}})
                    else:
                        await ctx.channel.send('Να μου γελάσεις ρε κοπελλούι; This challenge already exists!')
                else:
                    await ctx.channel.send('Not valid challenge category provided. !help for more info')
            else:
                await ctx.channel.send('Πεε που σου νέφκω που παεις... !ctf addchallenge takes 2 parameters. !help for more info.')
        else:
>>>>>>> master
            await ctx.channel.send('For this command you have to be in a channel created by !ctf create.')
            return

        challenge_name = params[0]
        category = params[1]
        if category not in CHALLENGE_CATEGORIES:
            await ctx.channel.send('Not valid challenge category provided. !help for more info')
            return

        chall_channel = discord.utils.get(
            ctx.channel.category.channels, name=channel_name + '-' + challenge_name)
        if chall_channel is not None:
            await ctx.channel.send('Να μου γελάσεις ρε κοπελλούι; This challenge already exists!')
            return

        overwrites = {
            self.guild.get_role(self.gid): discord.PermissionOverwrite(read_messages=False),
            self.bot.user: discord.PermissionOverwrite(read_messages=True),
            ctx.message.author: discord.PermissionOverwrite(read_messages=True)
        }
        await ctx.channel.category.create_text_channel(channel_name + "-" + challenge_name, overwrites=overwrites)

        new_challenge = Challenge(name=challenge_name, tags=[
                                  category], created_at=datetime.datetime.now())
        ctf.challenges.append(new_challenge)

        try:
            ctf.save()
        except:
            ctf.challenges.pop()
            await ctx.channel.send('Ουπς. Κάτι επήε λάθος.')
            return
        await ctx.channel.send('Εεεφτασέέέ!')

    @ctf.command()
    async def solve(self, ctx, *params):
<<<<<<< HEAD
        chall_name = '-'.join(ctx.channel.name.split('-')
                              [1:]) if '-' in ctx.channel.name else ''
        try:
            ctf = CTF.objects.get({'name': ctx.channel.category.name})
        except CTF.DoesNotExist:
            await ctx.channel.send('Ρε πελλοβρεμένε! Εν υπάρχει έτσι CTF.')
            return

        # Find challenge in CTF by name
        challenge = None
        for c in ctf.challenges:
            if c.name == chall_name:
                challenge = c
                break

        if not challenge:
=======
        chall_name = ctx.channel.name[len(ctx.channel.category.name)+1:] if '-' in ctx.channel.name else ""
        logger.info(chall_name)
        ctf_doc = serverdb.ctfs.find_one({"channelname": ctx.channel.category.name,
                                          "challenges":{"$elemMatch": {"name":chall_name} } })
        if ctf_doc != None: 
            if serverdb.ctfs.find_one({"channelname": ctx.channel.category.name,
                                        "challenges":{"$elemMatch": {"name":chall_name, "solved": True} } }) == None:
                
                solved_by = ', '.join([ctx.message.author.name] + [m.name for m in ctx.message.mentions])
                serverdb.ctfs.update_one(
                    {
                        "channelname": ctx.channel.category.name,
                        "challenges.name": chall_name
                    },
                    {"$set":{
                                "challenges.$.solved": True,
                                "challenges.$.solved_by": solved_by
                            } 
                        }
                )
                await ctx.channel.send('Πελλαμός! {0}! Contratz for solving {1}'.format(solved_by, chall_name))
            else:
                await ctx.channel.send('Άρκησες! This challenge has already been solved!')
        else:
>>>>>>> master
            await ctx.channel.send('Ρε πελλοβρεμένε! For this command you have to be in a ctf challenge channel created by `!ctf addchallenge`.')
            return

        if challenge.solved_at:
            await ctx.channel.send(f'Άρκησες! This challenge has already been solved by {", ".join(challenge.solved_by)}!')
            return

        challenge.solved_by = [ctx.message.author.name] + \
            [m.name for m in ctx.message.mentions]
        challenge.solved_at = datetime.datetime.now()

        try:
            ctf.save()
        except:
            await ctx.channel.send('Εσαντανώθηκα. Δοκίμασε ξανά ρε παρέα μου.')
            return

        await ctx.channel.send('Πελλαμός! {0}! Congrats for solving {1}. Έλα κουφεττούα :candy:'.format(ctx.message.author.name, chall_name))

    @ctf.command()
    async def join(self, ctx, *params):
        scat = '-'.join(list(params)).replace("'", "").lower()
        ctf_category = discord.utils.get(ctx.guild.categories, name=scat)
        if ctf_category != None:
            ctfrole = discord.utils.get(self.guild.roles, name='Team-'+scat)
            await ctx.message.author.add_roles(ctfrole)
        else:
            await ctx.channel.send('Εεεε!! Τι κάμνεις? There is no such CTF name. Use `!status`')

    @ctf.command()
    async def attempt(self, ctx, params):
        channel_name = str(ctx.channel.category)
        try:
            ctf = CTF.objects.get({'name': channel_name})
        except CTF.DoesNotExist:
            await ctx.channel.send('For this command you have to be in a channel created by !ctf create.')
            return

        chall_name = params
        chall_channel = discord.utils.get(
            ctx.channel.category.channels, name=channel_name + '-' + chall_name)
        if not chall_channel:
            await ctx.channel.send('Μα περιπέζεις μας; There is not such a challenge. Create it using !ctf addchallenge')
            return

        await chall_channel.set_permissions(ctx.message.author, read_messages=True)

        for ch in ctf.challenges:
            if ch.name == chall_name:
                # challenge solved already
                if ch.solved_at:
                    await ctx.channel.send(f'Ρε μπρο μου... Ελύσαμε το τουτο το challenge αφού.')
                    return
                # user already in attempted_by lsit
                if ctx.message.author.name in ch.attempted_by:
                    await ctx.channel.send(f'Ρε αρφούι μου... Είσαι ήδη μέσα στη λιστούα. [{", ".join(ch.attempted_by)}]')
                    return

                # TODO(investigate): ch.attempted_by.append(ctx.message.author.name) mutates all embedded challenges
                ch.attempted_by = ch.attempted_by + [ctx.message.author.name]
                try:
                    ctf.save()
                except:
                    await ctx.channel.send(f'Εν τα κατάφερα να σε βάλω μέσα στη λιστούα... Σόρρυ.')
                    return
                await ctx.channel.send(f'Άτε {ctx.message.author.name} μου! Έβαλα σε τζιαι στη λίστα τζείνων που μάχουνται πάνω στο challenge. [{", ".join(ch.attempted_by)}]')
                return

        await ctx.channel.send(f'Εν ήβρα έτσι challenge. Εν τα κατάφερα να σε βάλω μέσα στη λιστούα... Σόρρυ.')

    @ctf.command()
    async def description(self, ctx, *params):
        channel_name = str(ctx.channel.category)

        if len(params) is 0:
            await ctx.channel.send('Πεε που σου νέφκω που παεις... !ctf description takes parameters. !help for more info.')
            return

        try:
            ctf = CTF.objects.get({'name': channel_name})
        except CTF.DoesNotExist:
            await ctx.channel.send('For this command you have to be in a channel created by !ctf create.')
            return

        ctf.description = ' '.join(params)

        try:
            ctf.save()
        except:
            ctx.channel.send('Oops. Try setting the description again.')

        await ctx.channel.send('CTF description set!')

    @ctf.command()
    @commands.has_permissions(manage_channels=True, manage_roles=True)
    async def delete(self, ctx, *params):
        scat = '-'.join(list(params)).replace("'", "").lower()

        try:
            ctf = CTF.objects.get({'name': scat})
        except CTF.DoesNotExist:
            await ctx.channel.send('Ρε κουμπάρε! There is not any ongoing CTF with such a name.')
            return

        category = discord.utils.get(ctx.guild.categories, name=scat)
        if category is None:
            await ctx.channel.send('Ρε κουμπάρε! There is not any ongoing CTF with such a name.')
            return

        ctfrole = discord.utils.get(ctx.guild.roles, name='Team-'+scat)
        if ctfrole is not None:
            await ctfrole.delete()
        for c in category.channels:
            await c.delete()
        await category.delete()

        ctf.delete()

    @ctf.command()
    async def setcreds(self, ctx, *params):
        if len(params) != 2:
            await ctx.channel.send('Πεε που σου νέφκω που παεις... !ctf setcreds takes 2 parameters. !help for more info.')
            return

        channel_name = str(ctx.channel.category)
        try:
            ctf = CTF.objects.get({"name": channel_name})
        except CTF.DoesNotExist:
            await ctx.channel.send('For this command you have to be in a channel created by !ctf create.')
            return

        ctf.username = params[0]
        ctf.password = params[1]
        try:
            ctf.save()
        except:
            await ctx.channel.send('Ουπς. Έτα ούλα τζιαμέ...')
            return

        await ctx.channel.send('CTF shared credentials set!')

    @ctf.command()
    async def showcreds(self, ctx):
        channel_name = str(ctx.channel.category)
        try:
            ctf = CTF.objects.get({"name": channel_name})
        except CTF.DoesNotExist:
            await ctx.channel.send('For this command you have to be in a channel created by !ctf create.')
            return

        if not ctf.username or not ctf.password:
            await ctx.channel.send('This CTF has no shared credentials set!')
            return

        emb = discord.Embed(description=ctf.credentials(), colour=4387968)
        await ctx.channel.send(embed=emb)


def setup(bot):
    bot.add_cog(Ctf(bot))
