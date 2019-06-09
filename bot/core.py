import discord
import logging
import os
import sys

from discord.ext.commands import Bot
from discord.ext import commands
from discord.ext.commands.errors import MissingPermissions
from dotenv import load_dotenv
from help_info import *
from db_models import CTF, Challenge

load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot Extensions
extensions = ['ctf', 'manage', 'utils', 'ctftime']

client = discord.Client()
bot = commands.Bot(command_prefix='!')
bot.remove_command('help')

# Events

@bot.event
async def on_ready():
    logger.info(('<' + bot.user.name) + ' Online>')
    logger.info(discord.__version__)
    await bot.change_presence(activity=discord.Game(name='with your mind! Use !help'))

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
        await message.channel.send('Άφησ\' με! Μεν μου μάσσιεσε...')
    await bot.process_commands(message)

# Commands


@bot.command()
async def help(ctx, page=None):
    emb = discord.Embed(description=help_page, colour=4387968)
    await ctx.channel.send(embed=emb)


@bot.command()
async def status(ctx):
    status_response = ""
    ctfs = [c for c in ctx.guild.categories if c.name != 'Text Channels']
    sorted(ctfs, key=lambda x: x.created_at)
    for ctf in ctfs:
        try:
            ctf_doc = CTF.objects.get({"name": ctf.name})
            logger.info(ctf_doc.finished_at)
        except CTF.DoesNotExist:
            await ctx.channel.send(f"{ctf_doc.name} was not in the DB")
        ctfrole = discord.utils.get(ctx.guild.roles, name='Team-'+ctf.name)
        status_response += ctf_doc.status()

    if len(status_response) is 0:
        status_response = 'Μα σάννα τζιαι εν θωρώ κανένα CTF ρε παρέα μου.'
        await ctx.channel.send(status_response)
        return

    emb = discord.Embed(description=status_response, colour=4387968)
    await ctx.channel.send(embed=emb)

@bot.command()
async def frappe(ctx):
    await ctx.channel.send("Έφτασεεεεν ... Ρούφα τζαι έρκετε!")

@bot.command()
async def contribute(ctx):
    await ctx.channel.send("https://github.com/apogiatzis/KyriosZolo")

def run():
    sys.path.insert(1, os.getcwd() + '/extensions/')
    for extension in extensions:
        bot.load_extension(extension)
    bot.run(token)


if __name__ == '__main__':
    logger.info(token)
    run()
