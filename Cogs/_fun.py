import discord
from discord import User
from discord.app import user_command, slash_command
from discord.app.context import ApplicationContext
from discord.ext import commands


class Fun(commands.Cog, name="Fun Times"):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(
        name="clap", guild_ids=[689119429375819951], description="Claps someone's ass"
    )
    @commands.has_permissions(kick_members=True)
    async def clap(self, ctx: ApplicationContext, user: User):
        await ctx.respond(f"{ctx.author.mention} claps {user.mention}'s cheeks.")

    @user_command(guild_ids=[689119429375819951], name="Sup?")
    async def sup(self, ctx: ApplicationContext, user: User):
        await ctx.respond(f"{user.mention}\n{ctx.author.mention} says Sup?")


def setup(bot):
    bot.add_cog(Fun(bot))
