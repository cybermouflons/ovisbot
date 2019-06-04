import datetime
import discord
import logging
import sys

from discord.ext import commands
from db import *

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
            emb = discord.Embed(description=status_response, colour=4387968)
            await ctx.channel.send(embed=emb)
        else:
            await ctx.channel.send('Έφκαλεν η γλώσσα μου μαλιά ρε! For this command you have to be in a channel created by !ctf create.')

    @ctf.command()
    async def create(self, ctx, *params):
        scat = '-'.join(list(params)).replace("'", "").lower()
        category = discord.utils.get(ctx.guild.categories, name=scat)
        if category == None: # Checks if category exists, if it doesn't it will create it.
            user = ctx.message.author
            everyone_role = self.guild.get_role(self.gid)
            ctfrole = await self.guild.create_role(name='Team-'+scat, mentionable=True)
            await user.add_roles(ctfrole)
            overwrites = {
                self.guild.get_role(self.gid): discord.PermissionOverwrite(read_messages=False), #Everyone
                self.bot.user: discord.PermissionOverwrite(read_messages=True),
                ctfrole: discord.PermissionOverwrite(read_messages=True)
            }
            category = await self.guild.create_category(name=scat, overwrites=overwrites) #TODO: Manage permissions  overwrites={everyone_role: discord.Permissions.none (), ctfrole:523328
        else:
            await ctx.channel.send('Ρε κουμπάρε! This CTF name already exists! Pick another one')
            return
        await self.guild.create_text_channel(name='general', category=category)
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
            await ctx.channel.send('For this command you have to be in a channel created by !ctf create.')

    @ctf.command()
    async def solve(self, ctx, *params):
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
            await ctx.channel.send('Ρε πελλοβρεμένε! For this command you have to be in a ctf challenge channel created by `!ctf addchallenge`.')

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
    async def workon(self, ctx, params):
        channelname = str(ctx.channel.category)
        if serverdb.ctfs.find({"channelname": channelname}).count() > 0:
            chall_name = params
            chall_channel = discord.utils.get(ctx.channel.category.channels, name=channelname + '-' + chall_name)
            if chall_channel != None:
                await chall_channel.set_permissions(ctx.message.author, read_messages=True)
            else:
                await ctx.channel.send('Μα περιπέζεις μας; There is not such a challenge. Create it using !ctf addchallenge')
        else:
            await ctx.channel.send('For this command you have to be in a channel created by !ctf create.')
    
    @ctf.command()
    async def description(self, ctx, *params):
        channelname = str(ctx.channel.category)
        if serverdb.ctfs.find({"channelname": channelname}).count() > 0:
            if len(params) > 0:
                serverdb.ctfs.update_one({"channelname": channelname},
                                         {"$set": {"description": ' '.join(params)}})
                await ctx.channel.send('CTF description set!')
            else:
                await ctx.channel.send('Πεε που σου νέφκω που παεις... !ctf description takes parameters. !help for more info.')
        else:
            await ctx.channel.send('For this command you have to be in a channel created by !ctf create.')

    @ctf.command()
    @commands.has_permissions(manage_channels=True, manage_roles=True)
    async def delete(self, ctx, *params):
        scat = '-'.join(list(params)).replace("'", "").lower()
        category = discord.utils.get(ctx.guild.categories, name=scat)
        if category != None: # Checks if category exists, if it doesn't it will create it.
            ctfrole = discord.utils.get(ctx.guild.roles, name='Team-'+scat)
            if ctfrole != None: await ctfrole.delete()
            for c in category.channels:
                await c.delete()
            await category.delete()
            serverdb.ctfs.delete_one({"channelname":scat}) 
        else:
            await ctx.channel.send('Ρε κουμπάρε! There is not any ongoing CTF with such a name.')

    @ctf.command()
    async def setcreds(self, ctx, *params):
        channelname = str(ctx.channel.category)
        if serverdb.ctfs.find({"channelname": channelname}).count() > 0:
            if len(params) == 2:
                username = params[0]
                password = params[1]
                serverdb.ctfs.update_one({"channelname": channelname},
                                         {"$set": {"username": username, "password": password}})
                await ctx.channel.send('CTF shared credentials set!')
            else:
                await ctx.channel.send('Πεε που σου νέφκω που παεις... !ctf setcreds takes 2 parameters. !help for more info.')
        else:
            await ctx.channel.send('For this command you have to be in a channel created by !ctf create.')

    @ctf.command()
    async def showcreds(self, ctx):
        channelname = str(ctx.channel.category)
        ctf_doc = serverdb.ctfs.find_one({"channelname": channelname}) 
        if ctf_doc != None:
            if 'username' in ctf_doc and 'password' in ctf_doc:
                creds_response = """Username: %s
                                    Password: %s""" % (ctf_doc['username'], ctf_doc['password'])
                emb = discord.Embed(description=creds_response, colour=4387968)
                await ctx.channel.send(embed=emb)
            else:
                await ctx.channel.send('This CTF has no shared credentials set!')
        else:
            await ctx.channel.send('For this command you have to be in a channel created by !ctf create.')

def setup(bot):
    bot.add_cog(Ctf(bot))