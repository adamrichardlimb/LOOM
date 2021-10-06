"""
L.O.O.M (Let's Organise Our Mates)

LOOM is a helper bot for Basketweavers; a group of young men enthusiastic about basketweaving, among other interests. LOOM can assign people to Weaves, create new Weaves, and handle all of the niceties in between. i.e. Assigning to a Weave and introducing them to the other basketweavers.

author: Adam Richard Limb
version: 0.1
"""

#Begin with the necessary imports
import json
import os
import sys

import discord
from discord.ext.commands import Bot


#We have a config.json with the following fields:
#prefix         - bot prefix for commands
#token          - bot token for login
#application_id - the application id, going unused right now
#owners         - users who can call any command
#submissions    - the channel id for the submissions
#root           - the role id for the root role of the Weave tree
if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found! Please add it and try again.")
else:
    with open("config.json") as file:
        config = json.load(file)


#With config loaded - we can begin to initialise the bot
#We begin with setting up our intents - which specify what the bot can do
#We only need the defaults
intents = discord.Intents.default()
intents.members = True
bot = Bot(command_prefix=config["prefix"], intents=intents)

#TODO
#We want a custom help command so lets remove the default one
#bot.remove_command("help")

#Now bring in all our cogs - basically collections of commands
if __name__ == "__main__":
    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            extension = file[:-3]
            try:
                bot.load_extension(f"cogs.{extension}")
                print(f"Loaded extension '{extension}'")
            except Exception as e:
                exception = f"{type(e).__name__}: {e}"
                print(f"Failed to load extension {extension}\n{exception}") 


#With all our command brought in we can run the bot with the Token
bot.run(config["token"])