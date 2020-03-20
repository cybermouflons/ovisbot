import datetime, discord, logging, os, sys, dateutil.parser
import requests

from datetime import datetime, timezone, timedelta
from discord.ext import commands
from discord.ext import tasks
from discord.ext.commands.errors import MissingPermissions, CommandNotFound
from discord.ext.commands import Bot

from ovisbot.help_info import *
from ovisbot.helpers import chunkify, wolfram_simple_query
from ovisbot.db_models import CTF, Challenge

token = os.getenv("DISCORD_BOT_TOKEN")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot Extensions
extensions = ["ctf", "manage", "utils", "ctftime", "stats"]

client = discord.Client()
bot = commands.Bot(command_prefix="!")
bot.remove_command("help")

# Events


@bot.event
async def on_ready():
    logger.info(("<" + bot.user.name) + " Online>")
    logger.info(discord.__version__)
    await bot.change_presence(activity=discord.Game(name="with your mind! Use !help"))
    reminder.start()


@bot.event
async def on_command_error(ctx, error):
    # Handle missing permissions
    if isinstance(error, MissingPermissions):
        await ctx.channel.send(
            "Ops! You don't have sufficient permissions to do that. Τζίλα το πάρακατω..."
        )
    elif isinstance(error, CommandNotFound):
        await ctx.channel.send("Έφυε σου λλίο... Command not found")
    else:
        raise error


@bot.event
async def on_message(message):
    if bot.user in message.mentions:
        await message.channel.send("Άφησ' με! Μεν μου μάσσιεσαι...")
    await bot.process_commands(message)


@bot.event
async def on_message_edit(before, after):
    halfmin = 30  # time in seconds
    if (
        after.content != before.content
        and after.edited_at.timestamp() - after.created_at.timestamp() <= 30
    ):
        await bot.process_commands(after)


@bot.event
async def on_member_join(member):
    await member.send(
        "Καλώς τον/την! Εγώ είμαι ο Ζόλος τζαι καμνω τα ούλλα. Στείλε !help να πάρεις μιαν ιδέα."
    )
    announcements = discord.utils.get(member.guild.text_channels, name="announcements")
    if announcements != None:
        await announcements.send(
            (
                f"""Άτε {member.name} πε μας 2 λοούτθκια για σένα!! Τζαι τωρά στα εγγλέζικα:\nLadies and gentlemen we have grown! {member.name} tell us something about you!"""
            )
        )


# Commands


async def send_help_page(ctx, page):
    help_info = "--- " + page.upper() + " HELP PAGE ---\n" + help_page[page]
    while len(help_info) > 1900:  # Embed has a limit of 2048 chars
        idx = help_info.index("\n", 1900)
        emb = discord.Embed(description=help_info[:idx], colour=4387968)
        await ctx.author.send(embed=emb)
        summary = summary[idx:]
    emb = discord.Embed(description=help_info, colour=4387968)
    await ctx.author.send(embed=emb)


@bot.command()
async def help(ctx, *params):
    if isinstance(ctx.channel, discord.DMChannel):
        if len(params) > 0:
            for page in params:
                if page in help_page.keys():
                    await send_help_page(ctx, page)
                else:
                    await ctx.channel.send(
                        "Μπούκκα ρε Τσιούη! Εν υπάρχει ετσί page({0})\nAvailable pages: {1}".format(
                            page, " ".join(help_page.keys())
                        )
                    )
        else:
            for key in help_page.keys():
                await send_help_page(ctx, key)
    else:
        await ctx.channel.send("Κύριε Βειτερ!! Στείλε DM γιατί έπρησες μας τα!")


@bot.command()
async def status(ctx):
    status_response = ""
    non_ctf_categories = ["Text Channels","Voice Channels", "Round Table", "ECSC", "Casual", "Projects"]
    ctfs = [c for c in ctx.guild.categories if c.name not in non_ctf_categories]
    sorted(ctfs, key=lambda x: x.created_at)
    for ctf in ctfs:
        try:
            ctf_doc = CTF.objects.get({"name": ctf.name})
        except CTF.DoesNotExist:
            pass

        ctfrole = discord.utils.get(ctx.guild.roles, name='Team-'+ctf.name)
        status_response += ctf_doc.status(len(ctfrole.members))

    if len(status_response) is 0:
        status_response = "Μα σάννα τζιαι εν θωρώ κανένα CTF ρε παρέα μου."
        await ctx.channel.send(status_response)
        return

    for chunk in chunkify(status_response, 1900):
        emb = discord.Embed(description=chunk, colour=4387968)
        await ctx.channel.send(embed=emb)


@bot.command()
async def frappe(ctx):
    await ctx.channel.send("Έφτασεεεεν ... Ρούφα τζαι έρκετε!")


@bot.command()
async def wolfram(ctx, *params):
    query = " ".join(list(params))
    try:
        await ctx.channel.send(wolfram_simple_query(query))
    except Exception as e:
        logger.error(e)
        await ctx.channel.send("Σιέσε μέστην τιάνισην... Error!")


@bot.command()
async def chucknorris(ctx):
    joke_url = "http://api.icndb.com/jokes/random"
    response = requests.get(joke_url)
    data = response.json()
    await ctx.channel.send(data["value"]["joke"])


@bot.command()
async def contribute(ctx):
    await ctx.channel.send("https://github.com/apogiatzis/KyriosZolo")


def run():
    sys.path.insert(1, os.getcwd() + "/extensions/")
    for extension in extensions:
        bot.load_extension(extension)
    bot.run(token)


# tasks


@tasks.loop(seconds=1800)
async def reminder():
    guild = bot.guilds[0]
    categories = guild.by_category()
    ctfs = [
        c
        for c in guild.categories
        if c.name != "Text Channels" and c.name != "Voice Channels"
    ]

    for ctf in ctfs:
        try:
            ctf_doc = CTF.objects.get({"name": ctf.name})
            if ctf_doc.reminder:
                reminder_date = dateutil.parser.parse(ctf_doc.date_for_reminder)
                channel = discord.utils.get(ctf.channels, name="general")
                if datetime.now() > (reminder_date - timedelta(hours=1)):
                    alarm = (
                        (reminder_date.replace(microsecond=0))
                        - datetime.now().replace(microsecond=0)
                    ).minute
                    await channel.send(
                        f"⏰Ατέ μανα μου, ξυπνάτε το CTF ξεκινά σε {alarm} λεπτά!⏰"
                    )
                    ctf_doc.reminder = False
                    ctf_doc.save()
        except CTF.DoesNotExist:
            continue


if __name__ == "__main__":
    run()
