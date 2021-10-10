import discord
import logging
import glob
import os
import time
from sys import platform
from os import environ, listdir
from logging.handlers import RotatingFileHandler

# from discord import activity
# from discord import guild
from discord.ext.commands.help import MinimalHelpCommand
from dotenv import load_dotenv
from discord.ext import commands


start = time.perf_counter()
guilds_id = [
    689119429375819951,
]


class Manager(commands.Bot):
    def __init__(self):
        
        super().__init__(
            command_prefix="?",
            intents=discord.Intents.all(),
            owner_ids=[111252573054312448],
            help_command=commands.MinimalHelpCommand(),
            allow_mentions=discord.AllowedMentions.none(),
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name="Bug squasher.",
            ),
        )

        if os.path.exists("./Logs") is False:
            os.makedirs("./Logs")
        elif os.path.exists("./Logs/bot.log"):
            os.remove("./Logs/bot.log")
        else:
            pass

        logging.basicConfig(
            handlers=[
                RotatingFileHandler("./Logs/bot.log", maxBytes=5000000, backupCount=3)
            ],
            level=logging.DEBUG,
            format="%(asctime)s,%(msecs)d: %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
        )

        for filename in listdir("./Cogs"):
            if filename.endswith(".py") and not filename.startswith("_"):
                try:
                    self.load_extension(f"Cogs.{filename[:-3]}")
                    print(f"Cogs.{filename[:-3]} Loaded.")
                    logging.info(f"Cogs.{filename[:-3]} Loaded.")
                except Exception as e:
                    logging.info(e)
                    print(e)

    async def on_ready(self):
        if platform == "linux" or platform == "linux2":
            os.system("clear")
            print(
                f"Logged in as {self.user} ID:{self.user.id} after {round(time.perf_counter() - start,2)} seconds"
            )
            logging.info(
                f"Logged in as {self.user} ID:{self.user.id} after {round(time.perf_counter() - start, 2)} seconds"
            )
            print("--Pro Clubs Nation Bot v1.0---")
        elif platform == "win32":
            os.system("cls")
            print("--Pro Clubs Nation Bot v1.0---")
            print(
                f"Logged in as {self.user} ID:{self.user.id} after {round(time.perf_counter() - start, 1)} seconds"
            )
            logging.info(
                f"Logged in as {self.user} ID: {self.user.id} after {round(time.perf_counter() - start,1)} seconds"
            )


bot = Manager()
load_dotenv(".env")
bot.run(environ.get("TOKEN"))