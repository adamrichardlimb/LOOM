"""
fun.py is a cog containing all the
fun commands available in LOOM.

Things like incrementing the number of times woven,
displaying leaderboards and structure of Weaves, etc.
"""
import discord
from discord.ext import commands

from anytree import RenderTree
from anytree.importer import JsonImporter

class Fun(commands.Cog, name="Fun"):
  def __init__(self, bot):

        #Do our simple assignments first
        self.bot = bot
        self._last_member = None


  #Just a fun little command that shows you all the Weaves and how they link together
  @commands.command()
  async def basket(self, ctx):
    #Bring in our tree
    importer = JsonImporter()
    with open("weaves.json") as file:

      #This is an AnyNode - we need to convert them all to Weaves
      tree = importer.read(file)

    await ctx.send(RenderTree(tree).by_attr('name'))



#And here's our setup function - simply adds the cog to the bot
def setup(bot):
    bot.add_cog(Fun(bot))
