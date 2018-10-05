import discord
from discord.ext import commands

class Help():
    def __init__(self, bot):
        self.bot = bot

    async def change_message(self,author,message,i):
        if i == 0:
            cog = self.bot.cogsList[0]
            commands = self.bot.comsDict["No Cogs"]
        else:
            cog = self.bot.cogsList[i]
            commands = self.bot.comsDict[cog]
        em = discord.Embed(title = "Help", description = cog)
        for com in commands:
            em.add_field(name=com.signature,value=com.help,inline=False)
        await message.edit(embed=em)
        def check(reaction, user):
            return user == author and reaction.emoji in ('\U000025c0', '\U000025b6')
        reaction, user = await self.bot.wait_for("reaction_add",check=check,timeout=60)
        try:
            await message.remove_reaction(reaction.emoji,user)
        except:
            pass
        if reaction.emoji == '\U000025c0':
            if i == 0:
                i=10
                await self.change_message(author,message,i)
            else:
                i-=1
                await self.change_message(author,message,i)
        if reaction.emoji == '\U000025b6':
            if i == 10:
                i=0
                await self.change_message(author,message,i)
            else:
                i+=1
                await self.change_message(author,message,i)

        
    @commands.command()
    async def help(self,ctx, command=None):
        '''Shows this message'''
        self.bot.comsDict = {}
        self.bot.cogsList = []
        self.bot.no_cogs = []
        author = ctx.author
        i=0
        if command == None:
            for com in self.bot.commands:
                if com.cog_name == None:
                    self.bot.no_cogs.append(com)
                if com.cog_name in self.bot.cogsList:
                    pass
                else:
                    self.bot.comsDict.update({com.cog_name:self.bot.get_cog_commands(com.cog_name)})
                    self.bot.cogsList.append(com.cog_name)
            try:
                self.bot.comsDict.update({"No Cogs":self.bot.no_cogs})
                self.bot.cogsList.append("No Cogs")
                cog = self.bot.cogsList[0]
                commands = self.bot.comsDict["No Cogs"]
                em = discord.Embed(title = "Help", description = cog)
                for com in commands:
                    em.add_field(name=com.signature,value=com.help,inline=False)
                help_message = await ctx.send(embed=em)
                await help_message.add_reaction("\U000025c0")
                await help_message.add_reaction("\U000025b6")
                def check(reaction, user):
                    return user == ctx.author and reaction.emoji in ('\U000025c0', '\U000025b6')
                reaction,user = await self.bot.wait_for("reaction_add",check=check)
                try:
                    await help_message.remove_reaction(reaction,user)
                except:
                    pass
                if reaction.emoji == '\U000025c0':
                    if i == 0:
                        i= 10
                        await self.change_message(author,help_message,i)
                    else:
                        i-=1
                        await self.change_message(author,help_message,i)
                if reaction.emoji == '\U000025b6':
                    if i == 10:
                        i=0
                        await self.change_message(author,help_message,i)
                    else:
                        i+=1
                        await self.change_message(author,help_message,i)
            except KeyError:
                pass        
        if command != None:
            command = self.bot.get_command(command)
            await ctx.send("``"+command.signature+"``")

def setup(bot):
    bot.add_cog(Help(bot))