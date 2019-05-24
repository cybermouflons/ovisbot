import discord
import os
import sys

from discord.ext.commands import Bot
from discord.ext import commands
from discord.ext.commands.errors import MissingPermissions
from dotenv import load_dotenv
from help_info import *
from persistence import *

load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")

## Bot Extensions
extensions = ['ctf']

client = discord.Client()
bot = commands.Bot(command_prefix='!')
bot.remove_command('help')

## Events

@bot.event
async def on_ready():
    print(('<' + bot.user.name) + ' Online>')
    print(discord.__version__)
    await bot.change_presence(activity=discord.Game(name='with your mind'))

@bot.event
async def on_command_error(ctx, error):
    # Handle missing permissions
    if isinstance(error, MissingPermissions):
        await ctx.channel.send("Ops! You don't have sufficient permissions to do that. Τζίλα το πάρακατω...")
    else:
        raise error

@bot.event
async def on_message(message):
    if bot.user in message.mentions:
        await message.channel.send('Άφησ\'με! Μεν μου μάσσιεσε...')
    
    await bot.process_commands(message)

## Commands

@bot.command()
async def help(ctx, page=None):
    emb = discord.Embed(description=help_page, colour=4387968)
    emb.set_author(name='!request "x" - request a feature')
    await ctx.channel.send(embed=emb)

@bot.command()
async def status(ctx):
    emb = discord.Embed(description=help_page, colour=4387968)
    emb.set_author(name='CYberMouflons CTF Status')
    ctf_categories = [c for c in ctx.guild.categories if c.name != 'Text Channels']
    await ctx.channel.send(embed=emb)

def run():
    sys.path.insert(1, os.getcwd() + '/extensions/')
    for extension in extensions:
        bot.load_extension(extension)
    bot.run(token)

if __name__ == '__main__':
    run()