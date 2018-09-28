from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer
import discord
from discord.ext import commands

chatterbot = ChatBot("CapnBot")
chatterbot.set_trainer(ChatterBotCorpusTrainer)


class CapnChat():
    def __init__(self,bot):
        self.bot = bot

    @commands.command()
    async def cb(self,ctx,*,statement):
        '''Chatbot, input message and get response'''
        response = chatterbot.get_response(statement)
        await ctx.send(response)



def setup(bot):
    bot.add_cog(CapnChat(bot))