import discord
import logging
import sys

from discord.ext import commands
from db import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))

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
        serverdb.ctfs.insert_one({"channelname":scat})
    
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
            await ctx.channel.send('Re koumpare! There is not any ongoing CTF with such a name.')

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
                await ctx.channel.send('!ctf setcreds takes 2 parameters. !help for more info.')
        else:
            await ctx.channel.send('For this command you have to be in a channel created by !ctf create.')

    @ctf.command()
    async def showcreds(self, ctx):
        channelname = str(ctx.channel.category)
        ctf_doc = serverdb.ctfs.find_one({"channelname": channelname}) 
        if ctf_doc != None:
            if 'username' in ctf_doc and 'password' in ctf_doc:
                creds_response = """Username: %s
                                    Password: %s"""
                                     % (ctf_doc['username'], ctf_doc['password'])
                emb = discord.Embed(description=creds_response, colour=4387968)
                await ctx.channel.send(embed=emb)
            else:
                await ctx.channel.send('This CTF has no shared credentials set!')
        else:
            await ctx.channel.send('For this command you have to be in a channel created by !ctf create.')


def setup(bot):
    bot.add_cog(Ctf(bot))