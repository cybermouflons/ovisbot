import logging
import struct
from ctf import CHALLENGE_CATEGORIES
from db_models import CTF, Challenge
from discord.ext import commands

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Stats(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def stats(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid command passed. Use `!help`.')

    @stats.command()
    async def me(self, ctx):
        author = ctx.message.author.name
        ctfs = CTF.objects.aggregate(
            {"$match": {"challenges.solved_by": {"$eq": author}}},
            {"$unwind": "$challenges"},
            {"$match": {"challenges.solved_by": {"$eq": author}}}
        )

        categories_solved = {k: 0 for k in CHALLENGE_CATEGORIES}
        for ctf in ctfs:
            # only look at the first category tag - in case of multiple tags
            tag = ctf['challenges']['tags'][0]
            if tag.lower() not in categories_solved:
                continue
            categories_solved[tag] += 1

        sm = sum(categories_solved.values())
        mx = max(categories_solved.values())

        def normalize(v, mx, mn=0):
            if v == 0:
                return 0
            if mx == mn:
                return 1
            v = float(v)
            return (v - mn) / (mx - mn)

        def draw_bar(v, b=10):
            return (round(normalize(v, mx) * b) * '+').ljust(b, '-')

        to_ret = "\n".join([
            f'{draw_bar(categories_solved[k])} {k.upper()} x{categories_solved[k]}' for k in CHALLENGE_CATEGORIES
        ])

        preambles = [
            '👶 Είσαι νινί ακόμα.',  # 0-10 solved
            '👍 Κουτσά στραβά, κάτι καμνεις.',  # 10-20 solved
            '🐐👑 Μα εσού είσαι αρχιτράουλλος!'  # 20+ solved
        ]
        p_choice = preambles[min(int(sm/10), len(preambles)-1)]
        await ctx.send(f'{p_choice}\n```{to_ret}```')


def setup(bot):
    bot.add_cog(Stats(bot))
