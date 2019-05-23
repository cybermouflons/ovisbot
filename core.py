import discord
import os

from discord.ext.commands import Bot
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")

client = discord.Client()
bot = commands.Bot(command_prefix='!')
bot.remove_command('help')

@bot.event
async def on_ready():
    print(('<' + bot.user.name) + ' Online>')
    print(discord.__version__)
    await bot.change_presence(activity=discord.Game(name='Don’t everybody thank me at once.'))

@bot.event
async def on_message(message):
    if message.author != client.user:
        await message.channel.send(message.content[::-1])

if __name__ == '__main__':
    bot.run(token)