import discord

from discord.ext import commands

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
    
    # @commands.has_permissions(manage_channels=True)
    @ctf.command()
    async def create(self, ctx, *params):
        scat = '-'.join(list(params)).replace("'", "").lower()
        category = discord.utils.get(ctx.guild.categories, name=scat)
        if category == None: # Checks if category exists, if it doesn't it will create it.
            user = ctx.message.author
            everyone_role = self.guild.get_role(self.gid)
            ctfrole = await self.guild.create_role(name='Team-'+scat, mentionable=True)
            category = await self.guild.create_category(name=scat) #TODO: Manage permissions  overwrites={everyone_role: discord.Permissions.none (), ctfrole:523328
            await user.add_roles(ctfrole)
        else:
            await ctx.channel.send('Re koumpare! This CTF name already exists! Pick another one')
            return

        await self.guild.create_text_channel(name='general', category=category)
    
    @commands.has_permissions(manage_channels=True, manage_roles=True)
    @ctf.command()
    async def delete(self, ctx, *params):
        scat = '-'.join(list(params)).replace("'", "").lower()
        category = discord.utils.get(ctx.guild.categories, name=scat)
        if category != None: # Checks if category exists, if it doesn't it will create it.
            print(self.guild.roles)
            ctfrole = discord.utils.get(ctx.guild.roles, name='Team-'+scat)
            print(ctfrole)
            print(category.channels)
            for c in category.channels:
                await c.delete()
        else:
            await ctx.channel.send('Re koumpare! There is not any ongoing CTF with such a name.')

    @ctf.command()
    async def join(self, ctx):
        if teamdb[str(gid)].find_one({'name': str(ctx.message.channel)}):
            role = discord.utils.get(ctx.guild.roles, name=str(ctx.message.channel))
            user = ctx.message.author
            await user.add_roles(role)
            await ctx.send(f"{user} has joined the {str(ctx.message.channel)} team!")
        else:
            await ctx.send('You must be in a channel created using !ctf create to use this command!')
    

    

def setup(bot):
    bot.add_cog(Ctf(bot))