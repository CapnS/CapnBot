import discord
from discord.ext import commands

class Custom():
    def __init__(self,bot):
        self.bot = bot

    @commands.group()
    async def custom():
        pass

    @custom.command()
    async def add(self,ctx,name,*,response):

        
def setup(bot):
    bot.add_cog(Custom(bot))