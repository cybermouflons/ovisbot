import os
import logging

from ovisbot.helpers import escape_md
import ovisbot.locale as i118n
from pymodm import MongoModel, EmbeddedMongoModel, fields, connect
from ovisbot.utils.progressbar import draw_bar
from texttable import Texttable

logger = logging.getLogger(__name__)


class CogDetails(MongoModel):
    name = fields.CharField(required=True)
    local_path = fields.CharField(required=True)
    enabled = fields.BooleanField(default=True)
    loaded = fields.BooleanField(default=False)
    url = fields.CharField(required=False)
    description = fields.CharField(required=False)
    open_source = fields.BooleanField(default=True)

    def tolist(self):
        return [
            "✅" if self.enabled else "❌",
            "✅" if self.loaded else "❌",
            self.name,
            self.url if self.url else "BUILTIN",
            "YES" if self.open_source else "NO",
        ]


class BotConfig(MongoModel):
    REMINDERS_CHANNEL = fields.IntegerField(blank=True)
    IS_MAINTENANCE = fields.BooleanField()
    CTFTIME_TEAM_ID = fields.CharField()
    HTB_TEAM_ID = fields.CharField()
    ADMIN_ROLE = fields.CharField()
    EXTENSIONS = fields.EmbeddedDocumentListField(CogDetails, default=[])


class SSHKey(MongoModel):
    name = fields.CharField(required=True)
    owner_id = fields.CharField(required=True)
    owner_name = fields.CharField(required=True)
    private_key = fields.CharField(required=True)
    public_key = fields.CharField(required=True)

    def table_row_serialize(self):
        return [self.name, self.owner_name, self.public_key]

    @classmethod
    def table_serialize(cls):
        table = Texttable()
        table.set_deco(Texttable.HEADER)
        table.set_cols_dtype(["a", "a", "a"])  # automatic
        table.set_cols_align(["c", "c", "l"])
        table.add_rows(
            [
                ["name", "owner", "public_key_url"],
                *[key.table_row_serialize() for key in cls.objects.all()],
            ]
        )
        return table.draw()


class HTBUserMapping(MongoModel):
    discord_user_id = fields.IntegerField(required=True)
    htb_user = fields.CharField(required=True)
    htb_user_id = fields.IntegerField(required=True)


class CryptoHackUserMapping(MongoModel):
    discord_user_id = fields.IntegerField(required=True)
    cryptohack_user = fields.CharField(required=True)


class Challenge(EmbeddedMongoModel):
    name = fields.CharField(required=True)
    created_at = fields.DateTimeField(required=True)
    tags = fields.ListField(fields.CharField(), default=[])
    attempted_by = fields.ListField(fields.CharField(), default=[])
    solved_at = fields.DateTimeField(blank=True)
    solved_by = fields.ListField(fields.CharField(), default=[], blank=True)
    notebook_url = fields.CharField(default="", blank=True)
    flag = fields.CharField()


class CTF(MongoModel):
    name = fields.CharField(required=True)
    description = fields.CharField()
    created_at = fields.DateTimeField(required=True)
    finished_at = fields.DateTimeField()
    start_date = fields.DateTimeField()
    end_date = fields.DateTimeField()
    url = fields.URLField()
    username = fields.CharField()
    password = fields.CharField()
    challenges = fields.EmbeddedDocumentListField(Challenge, default=[], blank=True)
    pending_reminders = fields.ListField(blank=True, default=[])

    def status(self, members_joined_count):

        description_str = self.description + "\n" if self.description else ""

        solved_count = len(
            list(filter(lambda x: x.solved_at is not None, self.challenges))
        )
        total_count = len(self.challenges)
        status = (
            f":triangular_flag_on_post: **{self.name}** ({members_joined_count} Members joined)\n{description_str}"
            + f"```CSS\n{draw_bar(solved_count, total_count, style=5)}\n"
            + f" {solved_count} Solved / {total_count} Total"
        )
        if self.start_date:
            fmt_str = "%d/%m %H:\u200b%M"
            start_date_str = self.start_date.strftime(fmt_str)
            end_date_str = self.end_date.strftime(fmt_str) if self.end_date else "?"
            status += f"\n {start_date_str} - {end_date_str}\n"
        status += "```"
        return status

    def credentials(self):
        response = f":busts_in_silhouette: **Username**: {self.username}\n:key: **Password**: {self.password}"
        if self.url is not None:
            response += f"\n\nLogin Here: {self.url}"
        return response

    def challenge_summary(self):
        if not self.challenges:
            return i118n._(
                "No challenges found. Try adding one with `!ctf addchallenge <name> <category>`"
            )

        solved_response, unsolved_response = "", ""

        for challenge in self.challenges:
            challenge_details = f'**{escape_md(challenge.name[len(self.name)+1:])}** [{", ".join(challenge.tags)}]'
            if challenge.solved_at:
                solved_response += f':white_check_mark: {challenge_details} Solved by: [{", ".join(challenge.solved_by)}]\n'
            else:
                unsolved_response += f':thinking: {challenge_details} Attempted by: [{escape_md(", ".join(challenge.attempted_by))}]\n'

        return (
            f"\\>>> Solved\n{solved_response}" + f"\\>>> Unsolved\n{unsolved_response}"
        )

    class Meta:
        collection_name = "ctf"
        ignore_unknown_fields = True
