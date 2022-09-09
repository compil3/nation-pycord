# TODO: Create a gamertag/website register command so a player can /stats @DiscordName and look them up
from datetime import datetime
import logging
from dotenv.main import load_dotenv
import requests
import re

import discord
from discord.ext import commands
from discord.app.commands import slash_command
from discord.app import Option

import motor.motor_asyncio as motor

from os import environ
from .Extensions.paging import PaginatorView


default_player_url= "https://proclubsnation.com/wp-json/sportspress/v2/players?slug={}"
load_dotenv('.env')
cluster = motor.AsyncIOMotorClient(f"{environ.get('CONNECTION')}")
db = cluster["Nation"]
collection = db["registered"]
guild_id = [
    689119429375819951,
]
format = "%b %d %Y %I:%M%p"


class Register(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.has_role('Player')
    @slash_command(name="register", description="Register Discord to your Gamertag.\nHINT* Look at your player profile page url.\n('-' FOR SPACES)", guild_ids=guild_id)
    async def register(self, ctx, gamertag: str):
        await ctx.defer(ephemeral=True)
        _status = None

        try:
            exists = await collection.find_one({"_id": ctx.author.id})
            if exists is not None:
                _status = "Already Registered"
                await ctx.respond(f"{ctx.author.mention} You are already registered with: {exists['registered_gamer_tag']}.\n  If you are attempting to change your registered name (do to error or name change), please use ``/reset [gamertag]``.")
            else:
                current_time = datetime.now()
                reg_date = current_time.strftime(format)
                post = {
                    "_id": ctx.author.id,
                    "discord_full_name": f"{ctx.author.name}#{ctx.author.discriminator}",
                    "registered_gamer_tag": gamertag,
                    "gamer_tag_url": default_player_url.format(gamertag),
                    "date_registered": reg_date,
                }

                await collection.insert_one(post)
                _status = "Gamertag successfully registered."
            embed = discord.Embed(title="Registration System", description=_status)
            embed.set_author(name=f"{gamertag} Link", url=default_player_url.format(gamertag), icon_url="https://proclubsnation.com/wp-content/uploads/2020/08/PCN_logo_Best.png")
            embed.add_field(name="Gamertag", value=gamertag, inline=False)
            embed.add_field(name="Registration Date", value=reg_date, inline=False)
        except Exception as e:
            print(e)
        await ctx.respond(embed=embed)


    @commands.has_role("Player")
    @slash_command(name="reset", description="Re-register your Gamertag.", guild_ids=guild_id)
    async def reset(self, ctx, new_gamer_tag: str):
        await ctx.defer(ephemeral=True)
        _status=None
        try:
            exists = await collection.find_one({"_id": ctx.author.id})
            if exists is None:
                await ctx.respond(f"{ctx.author.mention}, you have not registered with the bot yet.  Please try /register instead.")
            else:
                _id = exists['_id']
                await collection.update_one({"_id": _id}, {'$set': {"registered_gamer_tag": new_gamer_tag}})
                await collection.update_one({"_id": _id}, {'$set': {"gamer_tag_url": default_player_url.format(new_gamer_tag)}})
            embed = discord.Embed(title="Registration System - Gamertag Change", description=_status)
            embed.set_author(name=f"{new_gamer_tag} Link", url=default_player_url.format(new_gamer_tag), icon_url="https://proclubsnation.com/wp-content/uploads/2020/08/PCN_logo_Best.png")
            embed.add_field(name="New Gamertag", value=new_gamer_tag, inline=False)
        except Exception as e:
            print(e)
        await ctx.respond(embed=embed)



def setup(bot):
    bot.add_cog(Register(bot))