import logging, datetime, os, requests
from discord.app.commands import SlashCommand, slash_command
import discord
from discord.ext.commands.help import Paginator
from pymongo import MongoClient, database
from discord.ext import commands

PASS = os.environ.get("PASS")
cluster = MongoClient(
    f"mongodb+srv://nation_user:{PASS}@cluster0.bhwnp.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
)
db = cluster["Nation"]
collection = db["verification"]
paginator = Paginator()
format = "%b %d %Y %I:%M%p"

guild_id = [
    689119429375819951,
]


class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(
        name="add",
        description="Add your Gamer-tag to the verification queue",
        guild_ids=guild_id,
    )
    async def add(self, ctx, gamertag: str):
        try:
            test_id = collection.find({"discord_id": ctx.author.id}).count() > 0
            embed = discord.Embed(title="Verification System")
            embed.set_author(
                name="Pro Clubs Nation",
                url="https://proclubsnation.com",
                icon_url="https://proclubsnation.com/wp-content/uploads/2020/08/PCN_logo_Best.png",
            )
            if test_id is True:
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
                    "discord_id": ctx.author.id,
                    "discord_name": ctx.author.name + "#" + ctx.author.discriminator,
                    "gamertag": gamertag,
                    "status": "In Queue",
                    "reason": "New",
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

    @slash_command(name="check", description="Check your verification status.", guild_ids=guild_id)
    @commands.has_role("New")
    async def check(self, ctx):
        result = collection.find({"discord_name": ctx.author.name + "#" + ctx.author.discriminator})
        for user in result:
            if user['status'] == 'Denied':
                try:
                    gt = user['gamertag']
                    embed = discord.Embed(color=ctx.author.color)
                    embed - discord.Embed(
                        title="PCN Discord Verification",
                        description=f"```Your GT: {gt} ```"
                    )
                    embed.add_field(name="Application Status", value=user['status'])
                    embed.add_field(name='Reason', value=user['reason'], inline=True)
                    embed.add_field(name='Updated', value=user['updated'], inline=False)
                    await ctx.author.send(embed=embed)
                    await ctx.send(f'{ctx.author.mention} Please check your DMs.', delete_after=5)
                    break
                except Exception as e:
                    await ctx.send(f"{ctx.author.mention}, DMs must be enabled to retreive the status of your verification.")
                    logging.info(f"User {ctx.author} does not have DMs enbled: {e}")
                    break
    
    @slash_command(name='queue', description="View verification queue.", guild_ids=guild_id)
    @commands.has_permissions(kick_members=True)
    async def queue(self, ctx):
        embeds = []
        result = collection.find({"status": "In Queue"})
        embed = discord.Embed(color=ctx.author.color)
        for user in result:
            embed = discord.Embed(
                title="PCN Discord Queue System",
                description=f"Gamer tag: ```{user['gamertag']}```"
            )
            embed.add_field(name="Discord User Name", value=user["discord_name"], inline=False)
            embed.add_field(name='Status', value=user['status'], inline=True)
            embed.add_field(name='Reason', value=user['reason'], inline=True)
            embed.add_field(name='Updated', value=user['updated'], inline=False)



def setup(bot):
    bot.add_cog(Verification(bot))
