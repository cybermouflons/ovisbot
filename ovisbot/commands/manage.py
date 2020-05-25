import asyncio
import discord
import logging
import os
import json
import ovisbot.locale as i118n

from discord.ext import commands
from functools import partial

from ovisbot import __version__
from ovisbot.cog_manager import CogAlreadyInstalledException
from ovisbot.helpers import success, failed
from ovisbot.db_models import CTF, SSHKey


logger = logging.getLogger(__name__)


class ManageCommandsMixin:
    # flake8: noqa: C901
    def load_commands(self):
        """Hooks commands with bot subclass"""
        bot = self

        @bot.group(hidden=True)
        @commands.has_role(bot.config.ADMIN_ROLE)
        async def manage(ctx):
            if ctx.invoked_subcommand is None:
                await ctx.send("Invalid command passed.  Use !help.")

        @manage.command()
        async def version(ctx):
            """Displays bot version"""
            await ctx.send("OvisBot: v{0}".format(__version__))

        @manage.command()
        async def showconfig(ctx):
            """Displays bot version"""
            await ctx.send("```{0}```".format(bot.config.__dict__))

        @manage.command()
        async def maintenance(ctx):
            """Enables/Disables maintenance mode"""
            self.config.IS_MAINTENANCE = not self.config.IS_MAINTENANCE
            self.config.save()
            await success(ctx.message)
            if self.config.IS_MAINTENANCE:
                await ctx.send("Maintenance mode enabled!")
            else:
                await ctx.send("Maintenance mode disabled!")

        @manage.group()
        async def config(ctx):
            """
            Group of commangs to manage bot configuration / Displays a config opions and values if run without a subcommand
            """
            if ctx.subcommand_passed == ctx.command.name:
                await ctx.send("```" + bot.config.options_table() + "```")
            else:
                if ctx.invoked_subcommand is None:
                    self.help_command.context = ctx
                    await failed(ctx.message)
                    await ctx.send(
                        i118n._("**Invalid command passed**. See below for more help")
                    )
                    await self.help_command.command_callback(
                        ctx, command=str(ctx.command)
                    )

        @config.command()
        async def set(ctx, option, value):
            """Sets given config variable"""
            if hasattr(self.config, option):
                value = type(value)(value)
                setattr(self.config, option, value)
                self.config.save()
                await success(ctx.message)
            else:
                await ctx.send(i118n._("Property {0} does not exist".format(option)))
                await failed(ctx.message)

        @manage.group()
        async def keys(ctx):
            """
            Group of commangs to manage extensions / Displays a list of all installed extensions if no subcommand passed
            """
            if ctx.subcommand_passed == ctx.command.name:
                await ctx.send("```" + SSHKey.table_serialize() + "```")
            else:
                if ctx.invoked_subcommand is None:
                    self.help_command.context = ctx
                    await failed(ctx.message)
                    await ctx.send(
                        i118n._("**Invalid command passed**. See below for more help")
                    )
                    await self.help_command.command_callback(
                        ctx, command=str(ctx.command)
                    )

        @keys.command()
        async def add(ctx, keyname):
            """Adds an SSH key"""
            try:
                SSHKey.objects.get({"name": keyname})
            except SSHKey.DoesNotExist:
                pass
            else:
                await ctx.send(
                    i118n._("This key name already exists. Choose another one.")
                )
                return

            if not isinstance(ctx.channel, discord.DMChannel):
                await ctx.send(
                    i118n._(
                        "This is a public channel. Continue the process through DM."
                    )
                )

            # TODO: Create key manager to handle these sort of tasks
            async def prompt_keys():
                """Creates coroutines to pick up private and public keys and saves key"""

                def is_key(add_key_msg, prefix, message):
                    return (
                        isinstance(message.channel, discord.DMChannel)
                        and add_key_msg.author == message.author
                        and message.content.startswith(prefix)
                        and message.attachments
                    )

                priv_prefix = "private"
                pub_prefix = "public"
                await ctx.author.send(
                    i118n._(
                        "Please upload your private and public keys an attachment in a message that starts with `{0}` and `{1}` respectively.".format(
                            priv_prefix, pub_prefix
                        )
                    )
                )

                async def wait_for_ssh_private_key(add_key_msg):
                    """Coroutine that waits for a private key to be uploaded"""
                    url = None
                    try:
                        message = await bot.wait_for(
                            "message",
                            timeout=60.0,
                            check=partial(is_key, add_key_msg, priv_prefix),
                        )
                    except asyncio.TimeoutError:
                        await ctx.author.send(
                            i118n._("Timed out... Try running `addkey` again")
                        )
                    else:
                        await ctx.author.send(
                            i118n._("Saved private key successfully!")
                        )
                        url = message.attachments[0].url
                    return url

                async def wait_for_ssh_public_key(add_key_msg):
                    """Coroutine that waits for a public key to be uploaded"""
                    url = None
                    try:
                        message = await bot.wait_for(
                            "message",
                            timeout=60.0,
                            check=partial(is_key, add_key_msg, pub_prefix),
                        )
                    except asyncio.TimeoutError:
                        await ctx.author.send(
                            i118n._("Timed out... Try running `addkey` again")
                        )
                    else:
                        await ctx.author.send(i118n._("Saved public key successfully!"))
                        url = message.attachments[0].url
                    return url

                privkey_prompt_task = bot.loop.create_task(
                    wait_for_ssh_private_key(ctx.message)
                )
                public_prompt_task = bot.loop.create_task(
                    wait_for_ssh_public_key(ctx.message)
                )

                # logger.info(type(task))
                private = await privkey_prompt_task
                public = await public_prompt_task

                key = SSHKey(
                    name=keyname,
                    owner_name=ctx.author.display_name,
                    owner_id=str(ctx.author.id),
                    private_key=private,
                    public_key=public,
                )
                key.save()

                message = await ctx.author.send(i118n._("Key added!"))
                await success(message)

            bot.loop.create_task(prompt_keys())

        @keys.command()
        async def rm(ctx, keyname):
            key = SSHKey.objects.get({"name": keyname})
            key.delete()
            await success(ctx.message)

        @manage.group()
        async def extensions(ctx):
            """
            Group of commangs to manage extensions / Displays a list of all installed extensions if no subcommand passed
            """
            if ctx.subcommand_passed == ctx.command.name:
                await ctx.send("```" + self.cog_manager.cog_table() + "```")
            else:
                if ctx.invoked_subcommand is None:
                    self.help_command.context = ctx
                    await failed(ctx.message)
                    await ctx.send(
                        i118n._("**Invalid command passed**. See below for more help")
                    )
                    await self.help_command.command_callback(
                        ctx, command=str(ctx.command)
                    )

        @extensions.command()
        async def disable(ctx, name):
            """Disables an installed extension"""
            self.cog_manager.disable_cog(name)
            await success(ctx.message)

        @extensions.command()
        async def enable(ctx, name):
            """Disables an installed extension"""
            self.cog_manager.enable_cog(name)
            await success(ctx.message)

        @extensions.command()
        async def reset(ctx):
            """Disables an installed extension"""
            self.cog_manager.reset()
            await success(ctx.message)

        @extensions.command()
        async def install(ctx, url, sshkey_name=None):
            """Installs a third party extension either by git url"""
            sshkey = SSHKey.objects.get({'name': sshkey_name}) if sshkey_name else None
            self.cog_manager.install_cog_by_git_url(url, sshkey)
            await success(ctx.message)

        @install.error
        async def install_error(ctx, err):
            if isinstance(err.original, CogAlreadyInstalledException):
                await ctx.channel.send(i118n._("Extension already installed"))
            elif isinstance(err.original, SSHKey.DoesNotExist):
                await ctx.channel.send(i118n._("This key does not exist."))
            await failed(ctx.message)

        @manage.command()
        @commands.has_permissions(administrator=True)
        async def dropctfs(self, ctx):
            """Deletes CTF collection"""
            CTF._mongometa.collection.drop()
            await ctx.channel.send("Πάππαλα τα CTFs....")
