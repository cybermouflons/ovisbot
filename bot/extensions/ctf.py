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
        self.challenges = {}
        self.ctfname = ""
        self.upcoming_l = []

    @commands.group()
    async def ctf(self, ctx):
        self.guild = ctx.guild
        self.gid = ctx.guild.id 

        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid command passed.  Use !help.')
    
    @ctf.command()
    async def status(self, ctx):
        ctx.channel.category.channels

    @ctf.command()
    async def create(self, ctx, *params):
        scat = '-'.join(list(params)).replace("'", "").lower()
        category = discord.utils.get(ctx.guild.categories, name=scat)
        if category == None: # Checks if category exists, if it doesn't it will create it.
            user = ctx.message.author
            everyone_role = self.guild.get_role(self.gid)
            ctfrole = await self.guild.create_role(name='Team-'+scat, mentionable=True)
            await user.add_roles(ctfrole)
            category = await self.guild.create_category(name=scat) #TODO: Manage permissions  overwrites={everyone_role: discord.Permissions.none (), ctfrole:523328
        else:
            await ctx.channel.send('Re koumpare! This CTF name already exists! Pick another one')
            return
        await self.guild.create_text_channel(name='general', category=category)
        serverdb.ctfs.insert_one({"channelname":scat, "active": True, "created_at": datetime.datetime.now()})

    @ctf.command()
    async def addchallenge(self, ctx, *params):
        channelname = str(ctx.channel.category)
        if serverdb.ctfs.find({"channelname": channelname}).count() > 0:
            if (len(params) == 2):
                chall_name = params[0]
                category = params[1]
                if category in CHALLENGE_CATEGORIES:
                    overwrites = {
                        self.guild.get_role(self.gid): discord.PermissionOverwrite(read_messages=False),
                        ctx.message.author: discord.PermissionOverwrite(read_messages=True)
                    }
                    await ctx.channel.category.create_text_channel(channelname + "-" + chall_name, overwrites=overwrites)
                else:
                    await ctx.channel.send('Not valid challenge category provided. !help for more info')
            else:
                await ctx.channel.send('Πεε που σου νέφκω που παεις... !ctf addchallenge takes 2 parameters. !help for more info.')
        else:
            await ctx.channel.send('For this command you have to be in a channel created by !ctf create.')

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
    async def description(self, ctx, params):
        channelname = str(ctx.channel.category)
        if serverdb.ctfs.find({"channelname": channelname}).count() > 0:
            if len(params) > 0:
                serverdb.ctfs.update_one({"channelname": channelname},
                                         {"$set": {"description": params}})
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