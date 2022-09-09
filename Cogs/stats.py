import logging
import requests
import re

import discord
from discord.ext import commands
from discord.app.commands import slash_command, user_command
from discord.app import Option

from .Extensions.paging import PaginatorView

import motor.motor_asyncio as motor
from dotenv import load_dotenv
from os import environ


load_dotenv('.env')

players = "https://proclubsnation.com/wp-json/sportspress/v2/players?slug={}"
teams = "https://proclubsnation.com/wp-json/sportspress/v2/teams"
tables = "https://proclubsnation.com/wp-json/sportspress/v2/tables"
guild_id = [689119429375819951,]

cluster = motor.AsyncIOMotorClient(f"{environ.get('CONNECTION')}")
db = cluster["Nation"]
collection = db["registered"]

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.has_role("Player")
    @slash_command(
        name="stats",
        description="Look up PCN Statistics for yourself or someone else.",
        guild_ids=guild_id
    )
    async def stats(self, ctx, gamertag: Option(str, "Player name", required=False)):
        await ctx.defer(ephemeral=True)
        if ctx.channel_id != 854348564444741682:
            await ctx.respond(
                f"{ctx.author.mention} you are attempting to use this command in the wrong channel.",
            )
            return
        await ctx.defer(ephemeral=True)
        post = []
        if gamertag is None:
            if " " in ctx.author.name:
                lookup = ctx.author.name.replace(" ", "-")
            else:
                lookup = ctx.author.name
            try:
                post = self.embed_builder(lookup)
                if post is not None:
                    view = PaginatorView(post, ctx)
                    view.message = await ctx.respond(
                        content="_ _", embed=post[0], view=view
                    )
                else:
                    await ctx.respond(
                        f"Sorry {ctx.author.mention}, we are unable to retrieve your stats.  Does your discord user name match your website name?"
                    )
                    return
            except Exception as e:
                logging.ERROR(e)
        else:
            if " " in gamertag:
                gamertag = gamertag.replace(" ", "-")
            try:
                post = self.embed_builder(gamertag)
                if post is None:
                    await ctx.respond(
                        f"Sorry {ctx.author.mention}, we are unable to retrieve the requested stats.  Please check the gamer tag and try again."
                    )
                    return
                else:
                    view = PaginatorView(post, ctx)
                    view.message = await ctx.respond(
                        content="_ _", embed=post[0], view=view
                    )
            except Exception as e:
                logging.ERROR(e)

    @commands.has_role('Player')
    @user_command(guild_ids=guild_id, name="Get Stats")
    async def get_stats_context(self, ctx, member: discord.Member):
        await ctx.defer(ephemeral=True)
        post = []
        try:
            registered_user = await collection.find_one({"_id": member.id})
            print(registered_user)
            if registered_user is None:
                await ctx.respond(f"{ctx.author.mention}, {member.name} hasn't registered with the bot yet. Feel free to mention it to them.")
            else:
                post = self.embed_builder(registered_user['registered_gamer_tag'])
                if post is not None:
                    view = PaginatorView(post, ctx)
                    view.message = await ctx.respond(
                        content="_ _", embed=post[0], view=view
                    )
                else:
                    await ctx.respond(
                        f"Sorry {ctx.author.mention}, we are unable to retrieve {member.mention}'s stats.  They most likely haven't registered with the bot yet.", 
                    )
                    return
        except Exception as e:
            print(e)


    def embed_builder(self, lookup):
        id = ["21", "27", "26"]
        embeds = []
        if " " in lookup:
            lookup = lookup.replace(" ", "-")
        try:
            url = players.format(lookup)
            player_page = requests.get(url)

            if len(player_page.json()) < 1:
                embeds = None
                return embeds
            else:
                player_record = player_page.json()[0]["statistics"]
                for key in id:
                    index = key
                    for field in player_record[index]:
                        if field != "0":
                            league_name = None
                            if index == "21":
                                league_name = "Super League"
                            elif index == "27":
                                league_name = "League One"
                            elif index == "26":
                                league_name = "League Two"
                            if (
                                field == "-1"
                                and "appearances" not in player_record[index][field]
                            ):
                                continue

                            if "&#8211;" in player_page.json()[0]["title"]["rendered"]:
                                player_name = player_page.json()[0]["title"]["rendered"]
                                playername, status = player_name.split("&#8211;")
                            else:
                                playername = player_page.json()[0]["title"]["rendered"]

                            win_record = str(
                                int(
                                    int(player_record[index][field]["appearances"])
                                    * float(player_record[index][field]["winratio"])
                                    / 100
                                )
                            )
                            draw_record = str(
                                int(
                                    int(player_record[index][field]["appearances"])
                                    * float(player_record[index][field]["drawratio"])
                                    / 100
                                )
                            )
                            loss_record = str(
                                int(
                                    int(player_record[index][field]["appearances"])
                                    * float(player_record[index][field]["lossratio"])
                                    / 100
                                )
                            )
                            windrawlost = (
                                win_record + "-" + draw_record + "-" + loss_record
                            )
                            ratio = (
                                str(player_record[index][field]["winratio"])
                                + "% - "
                                + str(player_record[index][field]["drawratio"])
                                + "% - "
                                + str(player_record[index][field]["lossratio"])
                                + "%"
                            )

                            # Check if the data exists or not.
                            if (
                                int(player_record[index][field]["appearances"]) < 1
                                and int(player_record[index][field]["shotsfaced"]) <= 0
                            ):
                                continue

                            # goalie stats & calculations
                            elif (
                                int(player_record[index][field]["shotsfaced"]) > 0
                                and float(player_record[index][field]["saveperc"]) > 0.0
                            ):
                                saveperc = (
                                    float(player_record[index][field]["saveperc"]) * 100
                                )
                                ga = float(player_record[index][field]["goalsagainst"])
                                mins = (
                                    float(player_record[index][field]["appearances"])
                                    * 90
                                )
                                gaa = float(ga / mins) * 90

                                if player_record[index][field]["name"] == "Total":
                                    embed = discord.Embed(
                                        title=f"**{league_name} - Career Totals**",
                                        color=0x1815C6,
                                    )
                                    embed.set_author(
                                        name=f"{playername}",
                                        url=f"{player_page.json()[0]['link']}stats",
                                    )
                                    if (
                                        "&#8211;"
                                        in player_page.json()[0]["title"]["rendered"]
                                    ):
                                        embed.set_footer(text=f"Status: {status}")
                                    pass
                                else:
                                    team_name_clean = re.compile("<.*?>")
                                    team = re.sub(
                                        team_name_clean,
                                        "",
                                        player_record[index][field]["team"],
                                    )
                                    team_link = re.search(
                                        r'href=[\'"]?([^\'" >]+)',
                                        player_record[index][field]["team"],
                                    )
                                    team_link_cleaned = team_link.group(0).replace(
                                        'href="', ""
                                    )
                                    embed = discord.Embed(
                                        title=f"**{team}** - {player_record[index][field]['name']}",
                                        url=team_link_cleaned,
                                        color=0x1815C6,
                                    )
                                    embed.set_author(
                                        name=f"{playername} - {league_name}",
                                        url=f"{player_page.json()[0]['link']}stats",
                                    )
                                    if (
                                        "&#8211;"
                                        in player_page.json()[0]["title"]["rendered"]
                                    ):
                                        embed.set_footer(text=f"Status: {status}")
                                embed.add_field(
                                    name="\u200B", value="```Record```", inline=False
                                )
                                embed.add_field(
                                    name="Appearances",
                                    value=player_record[index][field]["appearances"],
                                    inline=True,
                                )
                                embed.add_field(
                                    name="W-D-L", value=windrawlost, inline=True
                                )
                                embed.add_field(
                                    name="Win - Draw - Loss %", value=ratio, inline=True
                                )
                                embed.add_field(
                                    name="\u200b", value="```Stats```", inline=False
                                )
                                embed.add_field(
                                    name="Save %", value=saveperc, inline=True
                                )
                                embed.add_field(
                                    name="Shots Faced",
                                    value=player_record[index][field]["shotsfaced"],
                                    inline=True,
                                )
                                embed.add_field(
                                    name="Saves",
                                    value=player_record[index][field]["saves"],
                                    inline=True,
                                )
                                embed.add_field(
                                    name="GA",
                                    value=player_record[index][field]["goalsagainst"],
                                    inline=True,
                                )
                                embed.add_field(
                                    name="GAA", value=round(gaa, 2), inline=True
                                )
                                embed.add_field(
                                    name="CS",
                                    value=player_record[index][field]["cleansheets"],
                                    inline=True,
                                )
                                embed.add_field(
                                    name="\u200b", value="```Other```", inline=False
                                )
                                embed.add_field(
                                    name="Passes Completed",
                                    value=player_record[index][field][
                                        "passescompleted"
                                    ],
                                    inline=True,
                                )
                                embed.add_field(
                                    name="Pass Attempts",
                                    value=player_record[index][field][
                                        "passingattempts"
                                    ],
                                    inline=True,
                                )
                                embed.add_field(
                                    name="Pass %",
                                    value=f"{player_record[index][field]['passpercent']}%",
                                    inline=True,
                                )
                                embeds.append(embed)
                            # check if player isn't a goalie
                            elif (
                                int(player_record[index][field]["appearances"]) > 0
                                and float(player_record[index][field]["saveperc"])
                                == 0.00
                            ):
                                # player stats and calculations
                                avgPassPerGame = str(
                                    round(
                                        float(
                                            player_record[index][field][
                                                "passescompleted"
                                            ]
                                        )
                                        / float(
                                            player_record[index][field]["appearances"]
                                        ),
                                        2,
                                    )
                                )
                                tacklesPerGame = str(
                                    round(
                                        float(player_record[index][field]["tackles"])
                                        / float(
                                            player_record[index][field]["appearances"]
                                        ),
                                        2,
                                    )
                                )
                                interceptionsPerGame = str(
                                    round(
                                        float(
                                            player_record[index][field]["interceptions"]
                                        )
                                        / float(
                                            player_record[index][field]["appearances"]
                                        ),
                                        2,
                                    )
                                )
                                tckIntPerGame = (
                                    str(tacklesPerGame)
                                    + " - "
                                    + str(interceptionsPerGame)
                                )
                                possW = str(
                                    round(
                                        float(
                                            player_record[index][field][
                                                "possessionswon"
                                            ]
                                        )
                                    )
                                )
                                possL = str(
                                    player_record[index][field]["possessionslost"]
                                )
                                possession = possW + " - " + possL
                                if int(player_record[index][field]["goals"]) > 0:
                                    shotsPerGoal = (
                                        str(
                                            round(
                                                float(
                                                    player_record[index][field]["shots"]
                                                )
                                                / float(
                                                    player_record[index][field]["goals"]
                                                ),
                                                2,
                                            )
                                        )
                                        + " - "
                                        + str(player_record[index][field]["shpercent"])
                                        + "%"
                                    )
                                else:
                                    shotsPerGoal = (
                                        "0.0"
                                        + " - "
                                        + str(player_record[index][field]["shpercent"])
                                        + "%"
                                    )
                                if player_record[index][field]["name"] == "Total":
                                    embed = discord.Embed(
                                        title=f"**{league_name} - Career Totals**",
                                        color=0x1815C6,
                                    )
                                    embed.set_author(
                                        name=f"{playername} - {league_name}",
                                        url=f"{player_page.json()[0]['link']}stats",
                                    )
                                    if (
                                        "&#8211;"
                                        in player_page.json()[0]["title"]["rendered"]
                                    ):
                                        embed.set_footer(text=f"Status: {status}")
                                    pass
                                else:
                                    team_name_clean = re.compile("<.*?>")
                                    team = re.sub(
                                        team_name_clean,
                                        "",
                                        player_record[index][field]["team"],
                                    )
                                    team_link = re.search(
                                        r'href=[\'"]?([^\'" >]+)',
                                        player_record[index][field]["team"],
                                    )
                                    team_link_cleaned = team_link.group(0).replace(
                                        'href="', ""
                                    )
                                    embed = discord.Embed(
                                        title=f"**{team} - {player_record[index][field]['name']}**",
                                        url=team_link_cleaned,
                                        color=0x1815C6,
                                    )
                                    embed.set_author(
                                        name=f"{playername} - {league_name}",
                                        url=f"{player_page.json()[0]['link']}stats",
                                    )
                                    if (
                                        "&#8211;"
                                        in player_page.json()[0]["title"]["rendered"]
                                    ):
                                        embed.set_footer(text=f"Status: {status}")

                                embed.add_field(
                                    name="\u200B", value="```Record```", inline=False
                                )
                                embed.add_field(
                                    name="Appearances",
                                    value=player_record[index][field]["appearances"],
                                    inline=True,
                                )
                                embed.add_field(
                                    name="W-D-L", value=windrawlost, inline=True
                                )
                                embed.add_field(
                                    name="Win - Draw - Loss %", value=ratio, inline=True
                                )
                                embed.add_field(
                                    name="\u200b",
                                    value="```Offensive Stats```",
                                    inline=False,
                                )
                                embed.add_field(
                                    name="Goals",
                                    value=player_record[index][field]["goals"],
                                    inline=True,
                                )
                                embed.add_field(
                                    name="G/Game",
                                    value=player_record[index][field]["gpg"],
                                    inline=True,
                                )
                                embed.add_field(
                                    name="SOG - Shots",
                                    value=str(player_record[index][field]["sog"])
                                    + " - "
                                    + str(player_record[index][field]["shots"]),
                                    inline=True,
                                )
                                embed.add_field(
                                    name="S/Game",
                                    value=(
                                        str(
                                            round(
                                                float(
                                                    player_record[index][field]["shots"]
                                                )
                                                / float(
                                                    player_record[index][field][
                                                        "appearances"
                                                    ]
                                                ),
                                                2,
                                            )
                                        )
                                    ),
                                    inline=True,
                                )
                                embed.add_field(
                                    name="Shots/Goal - SH%",
                                    value=shotsPerGoal,
                                    inline=True,
                                )
                                embed.add_field(
                                    name="Assists",
                                    value=player_record[index][field]["assists"],
                                    inline=True,
                                )
                                embed.add_field(
                                    name="Passes - Pass Attempts",
                                    value=(
                                        str(
                                            player_record[index][field][
                                                "passescompleted"
                                            ]
                                        )
                                        + " - "
                                        + str(
                                            player_record[index][field][
                                                "passingattempts"
                                            ]
                                        )
                                    ),
                                    inline=True,
                                )
                                embed.add_field(
                                    name="Key Passes",
                                    value=player_record[index][field]["keypasses"],
                                    inline=True,
                                )
                                embed.add_field(
                                    name="Assists/Game",
                                    value=player_record[index][field]["apg"],
                                    inline=True,
                                )
                                embed.add_field(
                                    name="P/Game - Pass %",
                                    value=(
                                        str(avgPassPerGame)
                                        + " - "
                                        + str(
                                            player_record[index][field]["passpercent"]
                                        )
                                        + "%"
                                    ),
                                    inline=True,
                                )
                                embed.add_field(
                                    name="\u200b",
                                    value="```Defensive and Red Card Stats```",
                                    inline=False,
                                )
                                embed.add_field(
                                    name="Tackles",
                                    value=str(player_record[index][field]["tackles"]),
                                    inline=True,
                                )
                                embed.add_field(
                                    name="Interceptions",
                                    value=player_record[index][field]["interceptions"],
                                    inline=True,
                                )
                                embed.add_field(
                                    name="TKL-Int/Game",
                                    value=tckIntPerGame,
                                    inline=True,
                                )
                                embed.add_field(
                                    name="PossW - PossL", value=possession, inline=True
                                )
                                embed.add_field(
                                    name="Blocks",
                                    value=player_record[index][field]["blocks"],
                                )
                                embed.add_field(
                                    name="Headers Won",
                                    value=player_record[index][field]["headerswon"],
                                    inline=True,
                                )
                                embed.add_field(
                                    name="Clearances",
                                    value=player_record[index][field]["clearances"],
                                    inline=True,
                                )
                                embed.add_field(
                                    name="Cleansheets",
                                    value=player_record[index][field]["cleansheets"],
                                    inline=True,
                                )
                                embed.add_field(
                                    name="Red Cards",
                                    value=player_record[index][field]["redcards"],
                                    inline=True,
                                )
                                embeds.append(embed)
        except Exception as e:
            print(e)
        return embeds


def setup(bot):
    bot.add_cog(Stats(bot))
