import discord
import os
import sys

from discord.ext.commands import Bot
from discord.ext import commands
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

@bot.event
async def on_ready():
    print(('<' + bot.user.name) + ' Online>')
    print(discord.__version__)
    await bot.change_presence(activity=discord.Game(name='with your mind'))

@bot.command()
async def help(ctx, page=None):
    emb = discord.Embed(description=help_page, colour=4387968)
    emb.set_author(name='!request "x" - request a feature')

    await ctx.channel.send(embed=emb)

def run():
    sys.path.insert(1, os.getcwd() + '/extensions/')
    for extension in extensions:
        bot.load_extension(extension)
    bot.run(token)

if __name__ == '__main__':
    run()    