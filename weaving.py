"""
Weaving.py is a cog - a collection of commands, basically.
These are specifically for Weaving, the main commands of LOOM that will get the most use for necessary functionality of the bot.
"""

#Use these to bring in our config.json
import os
import sys
import json

#Use these to bring in our weaves.json
import anytree.search
from anytree import AnyNode
from anytree.importer import JsonImporter
from anytree.exporter import JsonExporter

#Use these to actually set up the discord bot
import discord
from discord.ext import commands

#First load config.json
if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found! Please add it and try again.")
else:
    with open("config.json") as file:
        config = json.load(file)

#Now create our weaves tree from weaves.json
if not os.path.isfile("weaves.json"):
    print("weaves.json not found! Creating one with parent Weave known as Weaver.")

    #Create root - known as Weaver
    #Role must be created in server and ID must be in config.json
    root = AnyNode(name="Weaver",
                   role=config["root"],
                   motto="",
                   threads=0,
                   size=0,
                   parent=None,
                   category=None)

    #Create our exporter
    exporter = JsonExporter(indent=2, sort_keys=True)
    with open("weaves.json", "w") as file:
        exporter.write(root, file)

#Now we know the file exists - we open it up
#Create our importer
importer = JsonImporter()
with open("weaves.json") as file:

    #This is an AnyNode - we need to convert them all to Weaves
    tree = importer.read(file)


#With config.json and weaves.json loaded - we continue.


#Here is our class proper
class Weaving(commands.Cog, name="Weaving"):
    def __init__(self, bot):

        #Do our simple assignments first
        self.bot = bot
        self._last_member = None


    @commands.command(help = "Approves an application in the applications channel, which can be set through !set_submissions or through altering the config.json.",

                     brief = "Approves an application in the applications channel.")
    @commands.has_role("Disciple of Weaving")
    async def accept(self, ctx, member: discord.Member, weave: discord.Role):

        if ctx.channel.id != config["submissions"]:
            #If command used outside of submissions channel, throw back warning.
            response = "Please only approve/reject submissions in the submissions channel"
            await ctx.channel.send(response)
        else:

            #First get the node the Weave belongs to
            current_node = anytree.search.find_by_attr(tree, weave.id, name='role', maxlevel=None)

            if not current_node:
                await ctx.send("No node for the Role mentioned! Make one with !create, or !assign.")
                return

            #Iterate up the tree
            while(current_node != None):
                role = discord.utils.get(ctx.guild.roles, id=current_node.role)
                await member.add_roles(role)
                current_node = current_node.parent


    @commands.command(help="Usage: !create [name] [@parent weave] Creates a weave attached to a parent.",
    brief = "Creates a weave.")
    @commands.has_role("Disciple of Weaving")
    async def create(self, ctx, weave, parent: discord.Role):

        parent_weave = anytree.search.find_by_attr(tree, parent.id, name='role', maxlevel=None)

        if not parent_weave:
            await ctx.send("Couldn't find parent weave! Did you mention it correctly?")
            return

        #If parent exists - create role and node in tree
        new_role = await ctx.guild.create_role(name=weave)

        #If parent is Weaver - then we need to create a new category and general for them.

        LOOM = discord.utils.get(ctx.guild.roles, name="LOOM")

        #Define our overwrites
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages = False),
            new_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            LOOM: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }

        if parent.id == config["root"]:
            #Create new category since subset of Weaver
            category = await ctx.guild.create_category(weave, overwrites=overwrites, reason=None)

            weave_name = weave + "-general"
        else:
            #Assign to parent category
            category = discord.utils.get(ctx.guild.categories, id=parent_weave.category)

            weave_name = weave

        #create channel
        channel = await ctx.guild.create_text_channel(weave_name, category = category, overwrites=overwrites)

        AnyNode(name=weave,
                role=new_role.id,
                size=0,
                threads=0,
                motto="",
                parent=parent_weave,
                category = category.id,
                channel = channel.id)

        #Create our exporter
        exporter = JsonExporter(indent=2, sort_keys=True)
        with open("weaves.json", "w") as file:
            #Save file
            exporter.write(tree, file)


    @commands.command(help = "Usage: !remove [@weave] Removes a weave, can add FALSE to the end in order to cull all children in the Weave below.",

    brief = "Removes a Weave by mention, use FALSE to cull all Weaves below as well.")
    @commands.has_role("Disciple of Weaving")
    async def remove(self, ctx, weave: discord.Role, save_children = "TRUE"):

        #Find node
        our_node = anytree.search.find_by_attr(tree, weave.id, name='role', maxlevel=None)

        #Now remove Weave from tree
        #We get the parent of our node
        parent      = our_node.parent

        #If parent is none then we have the root role, don't delete this
        if not parent:
            await ctx.send("You can't delete the root Weave! (If the role you are trying to delete is not the root Weave, please consult the bot administrator.)")
            return

        #Get children of parent and descendants of our_node as lists
        siblings    = list(parent.children)

        if save_children == "TRUE":
            children    = list(our_node.children)
        elif save_children == "FALSE":
            #save_children is false so delete all children as well

            #Generate empty list to append
            children    = []

            #Iterate through list and delete all roles and channels
            for child in our_node.descendants:
                role_to_delete = discord.utils.get(ctx.guild.roles, id=child.role)
                await role_to_delete.delete(reason = "Removed by: "+ ctx.message.author.name)

                chan_to_delete = discord.utils.get(ctx.guild.channels, id=child.channel)
                await chan_to_delete.delete(reason= "Removed by: " + ctx.message.author.name)
        else:
            await ctx.send("Parameter save_children was populated, but it wasn't set to FALSE. If you wish to delete and Weave AND ALL WEAVES BELOW IT, use !remove [@Weave] FALSE. If you wish to append all Weaves below it to the parent Weave, simply use !remove [@Weave]. If you'd like to see all of our Weaves, use !basket.")
            return


        #Remove our node and add our chidren to the list
        siblings.remove(our_node)
        parent.children = siblings + children

        #Now we have removed our Node delete the role and channel
        role_to_delete = discord.utils.get(ctx.guild.roles, id=our_node.role)
        await role_to_delete.delete(reason = "Removed by: "+ ctx.message.author.name)

        chan_to_delete = discord.utils.get(ctx.guild.channels, id=our_node.channel)
        await chan_to_delete.delete(reason= "Removed by: " + ctx.message.author.name)

        #Then finally if our parent node is Weaver - we should destroy the category as well
        if parent.role == config["root"]:
            ctgy_to_delete = discord.utils.get(ctx.guild.categories, id=our_node.category)
            await ctgy_to_delete.delete(reason= "Removed by: " + ctx.message.author.name)


        #Create our exporter
        exporter = JsonExporter(indent=2, sort_keys=True)
        with open("weaves.json", "w") as file:
            #Save file
            exporter.write(tree, file)

    @commands.command(
      help = "Assigns a role to a Weave, adding it to the Weave tree on the backend. Use only in a situation where a role exists, but does not exist on the Weave tree (viewable using !basket.) You must provide the channel the Weave should be assigned to, the category it should be listed under, and its parent Weave.",

      brief="Assigns a role, channel and parent to a Weave"
      )
    @commands.has_role("Disciple of Weaving")
    async def assign(self, ctx, role_to_assign: discord.Role, channel_to_assign: discord.TextChannel, parent_to_assign: discord.Role):

        #First check that the role isnt already assigned to another Weave.
        our_node = anytree.search.find_by_attr(tree, role_to_assign.id, name='role', maxlevel=None)

        if our_node:
            await ctx.send("Found " + role_to_assign.name + " assigned to a Weave! Remove the Weave first using !remove or contact a bot administrator!")
            return

        #If node doesn't exist - attempt to assign it.
        #Start by checking if the parent is Weaver.
        #If it is - find a category or create it.
        parent_node = anytree.search.find_by_attr(tree, parent_to_assign.id, name='role', maxlevel=None)

        if parent_node.role == config["root"]:
            category_to_assign = discord.utils.get(ctx.guild.categories, name=role_to_assign.name)

            if not category_to_assign:
                #If it doesnt exist - create it.
                LOOM = discord.utils.get(ctx.guild.roles, name="LOOM")
                overwrites = {
                  ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages = False),
                  role_to_assign: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                  LOOM: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                }

                category_to_assign = await ctx.guild.create_category(role_to_assign.name, overwrites=overwrites, reason=None)
        else:
            #If our parent node isnt weave - just grab the category of the node above us.
            category_to_assign = discord.utils.get(ctx.guild.categories, id=parent_node.category)

        #For good measure - assign the channel to the category provided
        await channel_to_assign.edit(category = category_to_assign)

        our_node = AnyNode(name=role_to_assign.name,
                           role=role_to_assign.id,
                           size=0,
                           threads=0,
                           motto="",
                           parent=parent_node,
                           category = category_to_assign.id,
                           channel = channel_to_assign.id)

        #Create our exporter
        exporter = JsonExporter(indent=2, sort_keys=True)
        with open("weaves.json", "w") as file:
            #Save file
            exporter.write(tree, file)



    @commands.command(help="Moves a Weave and all subweaves to a new parent.",

    brief="Moves a Weave to a new parent.")
    @commands.has_role("Disciple of Weaving")
    async def move(self, ctx, weave: discord.Role, parent: discord.Role):
        #First find our Weaves
        our_node = anytree.search.find_by_attr(tree, weave.id, name='role', maxlevel=None)

        if not our_node:
            await ctx.send("Couldn't find Weave "+ weave.name + " in Weave tree, use !assign to put it in tree!")
            return

        parent_node = anytree.search.find_by_attr(tree, parent.id, name='role', maxlevel=None)

        if not parent_node:
            await ctx.send("Couldn't find parent Weave "+ parent.name + " in Weave tree, use !assign to put it in tree!")
            return

        #If current parent node is weaver - and new parent node is not weaver
        #Then delete category
        if (parent_node.role != config["root"]) and (our_node.parent.role == config["root"]):
            #Get our category
            current_category = discord.utils.get(ctx.guild.categories, id=our_node.category)
            #Delete it
            await current_category.delete(reason= "Deleted by moving.")

        #Now we know both our weave and parent are in the tree - lets simply assign the parent of our weave
        our_node.parent = parent_node

        #Then assign the parent category for good measure
        if parent_node.category:
            our_node.category = parent_node.category
        else:
            #If parent category doesnt exist - then create new category
            #We wont force them to keep up the naming convention for Weaves primarily under Weaver because they are explicitly asking for this change - we'll assume they know what theyre doing. If they want [weave-general] they can rename it themselves.
            LOOM = discord.utils.get(ctx.guild.roles, name="LOOM")
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages = False),
                weave: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                LOOM: discord.PermissionOverwrite(read_messages=True, send_messages=True)
              }

            new_category = await ctx.guild.create_category(weave.name, overwrites=overwrites, reason=None)

            our_node.category = new_category.id

        #Get the channel associated with the node
        channel = discord.utils.get(ctx.guild.channels, id=our_node.channel)
        category_to_assign = discord.utils.get(ctx.guild.categories, id=our_node.category)

        #Assign it the new category
        await channel.edit(category = category_to_assign)

        #Now assign category to all child nodes also
        children = our_node.descendants
        for child in children:
            #Assign to node value
            child.category = our_node.category

            #Then edit channels associated with child
            child_channel = discord.utils.get(ctx.guild.channels, id=child.channel)
            await child_channel.edit(category = category_to_assign)

        #Create our exporter
        exporter = JsonExporter(indent=2, sort_keys=True)
        with open("weaves.json", "w") as file:
            #Save file
            exporter.write(tree, file)




#And here's our setup function - simply adds the cog to the bot
def setup(bot):
  bot.add_cog( Weaving(bot))
