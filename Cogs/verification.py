import discord
from discord import interactions
from discord.ext import commands
from discord.app.commands import SlashCommand, slash_command

import logging, datetime, os, requests
from dotenv.main import load_dotenv
from os import environ
from pymongo.message import delete

from pymongo import MongoClient
from .Extensions.paging import PaginatorView
import motor.motor_asyncio as motor


# PASS = os.environ.get("PASS")
load_dotenv(".env")
PASS = environ.get("MONGO_BOT_PASS")
print(PASS)
# cluster = MongoClient(
#     f"mongodb+srv://pcn_bot:{PASS}@cluster0.bhwnp.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
# )
cluster = motor.AsyncIOMotorClient(f"{environ.get('CONNECTION')}")
db = cluster["Nation"]
collection = db["verification"]
format = "%b %d %Y %I:%M%p"
# paginator = Paginator
guild_id = [
    689119429375819951,
]


class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # TODO: Fix up all the queries

    @slash_command(
        name="add",
        description="Add your Gamer-tag to the verification queue",
        guild_ids=guild_id,
    )
    async def add(self, ctx, gamertag: str):
        await ctx.defer(ephemeral=True)
        try:
            test_id = collection.find({"discord_id": ctx.author.id}).count() > 0
            embed = discord.Embed(title="Verification System")
            embed.set_author(
                name="Pro Clubs Nation",
                url="https://proclubsnation.com",
                icon_url="https://proclubsnation.com/wp-content/uploads/2020/08/PCN_logo_Best.png",
            )
            if test_id:
                results = collection.find({"discord_id": ctx.author.id})
                for user in results:
                    embed.description = "You are already in the queue.  Please be patient while we process requests on a first-come, first-serve basis."
                    embed.add_field(name="Status", value=user["status"])
                    embed.add_field(name="Reason", value=user["reason"])
                    embed.set_footer(text="proclubsnation.com")
                    break
            else:
                now = datetime.datetime.now()
                tstamp = now.strftime(format)
                post = {
                    "_id": ctx.author.id,
                    "discord_name": f"{ctx.author.name}#{ctx.author.discriminator}",
                    "gamertag": gamertag,
                    "status": "In Queue",
                    "reason": "New Application",
                    "updated": tstamp,
                }

                collection.insert_one(post)
                embed.add_field(
                    name="Status",
                    value="You have been added to the queue.  Please be patient while we process requests on a first-come, first-server basis.",
                )
        except Exception as e:
            logging.error(e)
        await ctx.respond(embed=embed)

    @slash_command(
        name="check", description="Check your verification status.", guild_ids=guild_id
    )
    @commands.has_role("New")
    async def check(self, ctx):
        await ctx.defer(ephemeral=True)
        _status = None
        try:
            applicant = await collection.find_one({"_id": ctx.author.id})

            if applicant["_id"] == ctx.author.id:
                if applicant["status"] == "Denied":
                    _status = f"**Status:*** :no_entry:  **{applicant['status']}**"
                    _reason = applicant["reason"]
                else:
                    _status = f"**Status**: :warning: **{applicant['status']}**"
                    _reason = f"**{applicant['reason']}**"
                _updated = applicant["updated"]
            else:
                print("Error")
            embed = discord.Embed(color=ctx.author.color)
            embed = discord.Embed(
                title="PCN Discord Verification Status", description=_status
            )
            embed.add_field(name="**Reason**", value=_reason, inline=False)
            embed.add_field(name="Last Updated", value=_updated, inline=False)

        except Exception as e:
            print(e)
        await ctx.respond(embed=embed, ephemeral=True)

    # TODO: Add buttons to Approve/Deny etc and then ask for a reason if Denied/Pending Reviewed/Waiting etc
    @slash_command(
        name="queue", description="View verification queue.", guild_ids=guild_id
    )
    @commands.has_permissions(kick_members=True)
    async def queue(self, ctx):
        print("Entered queue command")
        await ctx.defer(ephemeral=True)

        embeds = []
        result = collection.find({"status": "In Queue"})
        embed = discord.Embed(color=ctx.author.color)
        for user in result:
            embed = discord.Embed(
                title="PCN Discord Queue System",
                description=f"Gamer tag: ```{user['gamertag']}```",
            )
            embed.add_field(
                name="Discord User Name", value=user["discord_name"], inline=False
            )
            embed.add_field(name="Status", value=user["status"], inline=True)
            embed.add_field(name="Reason", value=user["reason"], inline=True)
            embed.add_field(name="Updated", value=user["updated"], inline=False)
            embed.set_footer(text=f"Discord ID: {user['discord_id']}")
            embeds.append(embed)
        try:
            view = PaginatorView(embeds, ctx)
            # await ctx.respond(embed=embeds[0], view=view)
            # view.message = await ctx.original_message()
            view.message = await ctx.respond(content="_ _", embed=embeds[0], view=view)
        except Exception as e:
            print(e)

    @commands.has_permissions(kick_members=True)
    @slash_command(
        name="approve", description="Approve member application", guild_id=guild_id
    )
    async def approve(self, ctx, member: discord.Member = None):
        try:
            await ctx.defer(ephemeral=True)
            member = discord.Guild.get_member(id)
            _user = f"{member.name}#{member.discriminator}"
            now = datetime.datetime.now()
            tstamp = now.strftime(format)

            if collection.find({"discord_name": _user}).count() < 1:
                await ctx.send(
                    f"{member.name} not found.  Please try again or contact Spillshot",
                    delete_after=5,
                )
            else:
                collection.update(
                    {"discord_name": _user},
                    {
                        "$set": {
                            "status": "Completed",
                            "reason": "Approved",
                            "updated": tstamp,
                        }
                    },
                )
                await member.remove_roles(843896103686766632)
                await member.add_roles(843899510483976233)
                await ctx.respond(f"{member.name} approved.", delete_after=5)
                await ctx.member.send("You have been approved in Discord.")
        except Exception as e:
            print(e)

    @commands.has_permissions(kick_members=True)
    @slash_command(
        name="deny", description="Deny member application", guild_ids=guild_id
    )
    async def deny(self, ctx, member: discord.Member, reason: str):

        await ctx.defer(ephemeral=True)
        _user = f"{member.name}#{member.discriminator}"
        now = datetime.datetime.now()
        tstamp = now.strftime(format)

        if collection.find({"discord_name": _user}).count() < 1:
            await ctx.respond(f"{member.name} not found.  Please try again.")
        else:
            collection.update(
                {"discord_name": _user},
                {"$set": {"status": "Denied", "reason": reason, "updated": tstamp}},
            )
            await ctx.respond(f"{member.name} updated.")


def setup(bot):
    bot.add_cog(Verification(bot))
