import discord
from discord import channel
from discord.ext import commands

import settings
import logging

from re import compile as re_compile


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.Command):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(
                f"{ctx.author.mention} the command is not found.", delete_after=3
            )
            return
        if isinstance(error, commands.DisabledCommand):
            await ctx.send(
                f"{ctx.author.mention} the command is disabled", delete_after=3
            )
            return
        if isinstance(error, commands.CommandError):
            raise error
        await ctx.send(
            embed=discord.Embed(
                title=" ".join(
                    re_compile(r"[A-Z][a-z]*").findall(error.__class__.__name__)
                ),
                description=str(error),
                color=discord.Color.red(),
            )
        )
        # logging.error(f"ERR THROWN:\n {re_compile(r"[A-Z][a-z]*").findall(error.__class__.__name__))

        # if isinstance(error, commands.MissingRequiredArgument):
        #     logging.warning(f'{ctx.author} used {ctx.command} incorrectly.  Reason: {error}.')
        # else:
        #     logging.warning(f"{ctx.author} used {ctx.command}.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        try:
            if message.channel.type.name == "private":
                return
            elif message.channel.type.name == "text":
                if (
                    message.author.get_role(842505724458172467)
                    or message.author.id is self.bot.user.id
                ):
                    await self.bot.process_commands(message)
                else:
                    await message.delete()
        except Exception as e:
            print(e)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        logging.info(
            f"\nA message was deleted.\nAuthor: {message.author}\nContent:{message.content}"
        )


def setup(bot):
    bot.add_cog(Events(bot))
