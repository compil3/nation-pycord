import logging
import discord
import os
import asyncio
import traceback

import settings

from discord.app import slash_command
from discord.errors import ExtensionAlreadyLoaded, ExtensionFailed, ExtensionNotFound
from discord.ext import commands


class Admin(commands.Cog):
    def __init__(self, bot) -> None:
        super().__init__()
        self.bot = bot
        logging.info("Initialized Cog")

    @slash_command(
        name="reload",
        guild_ids=settings.GUILD_IDS,
        description="Reloads all available cogs.",
    )
    @commands.has_permissions(kick_members=True)
    async def reload(self, ctx):
        if ctx.author.id != 111252573054312448:
            return

        await ctx.defer()
        embed = discord.Embed(title="Reloading all cogs!", color=0x808080)
        for ext in os.listdir("./Cogs"):
            if ext.endswith(".py") and not ext.startswith(("_")):
                try:
                    self.bot.reload_extension(f"Cogs.{ext[:-3]}")
                    embed.add_field(
                        name=f"Reloaded: ``{ext}``", value="\uFEFF", inline=False
                    )
                except Exception as e:
                    embed.add_field(
                        name=f"Failed to load ``{ext}``", value=e, inline=False
                    )
                    logging.error(e)
                await asyncio.sleep(0, 5)
        await ctx.respond(embed=embed)

    @slash_command(
        name="load", guild_ids=settings.GUILD_IDS, description="Loads a Cog."
    )
    @commands.is_owner()
    async def load(self, ctx, *, module):
        try:
            if ".py" not in module:
                module = module + ".py"
            else:
                pass
            self.bot.load_extension(f"Cogs.{module[:-3]}")
            e = discord.Embed(description=f"``{module}`` has been loaded.")
            await ctx.respond(embed=e, delete_after=3)
        except ExtensionAlreadyLoaded as el:
            await ctx.respond(embed=el, delete_after=3)
        except ExtensionNotFound as enf:
            await ctx.respond(embed=enf, delete_after=3)
        except ExtensionFailed as ef:
            await ctx.repond(embed=ef, delete_after=3)
            e = discord.Embed(description=traceback.format_exc())


def setup(bot):
    bot.add_cog(Admin(bot))
