from asyncio import tasks
import logging
import asyncio
from re import S
import ssl
import aiohttp

import discord
from discord.ext import commands
from discord.app.commands import slash_command
from .Extensions.paging import PaginatorView

from operator import indexOf, le, pos


format = "%b %d %Y %I:%M%p"
guild_id = [689119429375819951]
tables = "https://proclubsnation.com/wp-json/sportspress/v2/tables?slug={}"
competitions = ["super-league", "league-one", "league-two"]


class Tables(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_leagues(session):
        tasks = []
        for league in competitions:
            tasks.append(session.get(tables.format(league), ssl=False))
        return tasks

    async def get_tables(self, mobile):
        embeds = []
        league_table = []

        async with aiohttp.ClientSession() as session:
            tasks = Tables.get_leagues(session)
            tables = await asyncio.gather(*tasks)
            for standings in tables:
                league_table.append(await standings.json())
            for index in league_table:
                team_standing = []
                team_points = []

                # print(index[0]['data'])
                league_name, season = index[0]["title"]["rendered"].split("&#8211;")
                embed = discord.Embed(title=f"**{season}**", color=0x1815C6)
                for table_position in index[0]["data"]:
                    if table_position != "0":
                        if mobile == False:
                            team_standing.append(
                                str(index[0]["data"][table_position]["pos"])
                                + ". "
                                + str(index[0]["data"][table_position]["name"])
                                + "\n"
                            )
                            team_points.append(
                                str(index[0]["data"][table_position]["pts"]) + "\n"
                            )
                        else:
                            team_standing.append(
                                str(index[0]["data"][table_position]["pos"])
                                + ". "
                                + str(index[0]["data"][table_position]["name"])
                                + "        | "
                                + str(index[0]["data"][table_position]["pts"])
                                + "\n"
                            )
                            team_points.append(
                                str(index[0]["data"][table_position]["pts"]) + "\n"
                            )
                team_ranking = " ".join(team_standing)
                team_pts = " ".join(team_points)
                embed.set_author(name=f"{league_name}", url=index[0]["link"])
                if mobile == True:
                    embed.add_field(name="Rank - Pts", value=team_standing, inline=True)
                else:
                    embed.add_field(name="Rank", value=team_ranking, inline=True)
                    embed.add_field(name="Pts", value=team_pts, inline=True)

                embeds.append(embed)
        return embeds

    @commands.has_role("Player")
    @slash_command(name="tables", description="PCN Standings", guild_ids=guild_id)
    async def table(self, ctx):
        await ctx.defer(ephemeral=True)
        post = []

        if ctx.channel.id != 854348564444741682:
            await ctx.respond(
                f"{ctx.author.mention} you are attempting to use the command in the wrong channel.",
                delete_after=5,
            )
            return
        else:
            try:
                post = await Tables.get_tables(self, ctx.author.is_on_mobile())
                # post = self.table_builder()
                view = PaginatorView(post, ctx)
                view.message = await ctx.respond(
                    content="_ _", embed=post[0], view=view
                )
            except Exception as e:
                logging.ERROR(f"Error in tables.py: {e}")
                print(e)


def setup(bot):
    bot.add_cog(Tables(bot))
