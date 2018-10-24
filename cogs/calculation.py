import discord
from discord.ext import commands
import math
import sympy

class Math():

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def add(self, ctx, first, second):
        '''Adds two numbers'''
        answer = float(first) + float(second)
        await ctx.send(str(answer))

    @commands.command()
    async def subtract(self, ctx, first, second):
        '''Subtracts two numbers'''
        answer = float(first) - float(second)
        await ctx.send(str(answer))

    @commands.command()
    async def multiply(self, ctx, first, second):
        '''Multiplies two numbers'''
        answer = float(first) * float(second)
        await ctx.send(str(answer))

    @commands.command()
    async def divide(self, ctx, first, second):
        '''Divides two numbers'''
        answer = float(first) / float(second)
        await ctx.send(str(answer))

    @commands.command()
    async def sin(self, ctx, number):
        '''Gives the sin of a number'''
        answer = math.sin(float(number))
        await ctx.send(str(answer))

    @commands.command()
    async def cos(self, ctx, number):
        '''Gives the cos of a number'''
        answer = math.cos(float(number))
        await ctx.send(str(answer))

    @commands.command()
    async def tan(self, ctx, number):
        '''Gives the tan of a number'''
        answer = math.tan(float(number))
        await ctx.send(str(answer))

    @commands.command()
    async def arcsin(self, ctx, number):
        '''Gives the arcsin of a number'''
        try:
            answer = math.asin(float(number))
        except ValueError:
            await ctx.send('Domain Error')
        await ctx.send(str(answer))

    @commands.command()
    async def arccos(self, ctx, number):
        '''Gives the arccos of a number'''
        try:
            answer = math.acos(float(number))
        except ValueError:
            await ctx.send('Domain Error')
        await ctx.send(str(answer))

    @commands.command()
    async def arctan(self, ctx, number):
        '''Gives the arctan of a number'''
        try:
            answer = math.atan(float(number))
        except ValueError:
            await ctx.send('Domain Error')
        await ctx.send(str(answer))

    @commands.command()
    async def solve(self,ctx,*,equation):
        answer = sympy.solvers.solve(equation,"x")
        await ctx.send(answer)

def setup(bot):
    bot.add_cog(Math(bot))