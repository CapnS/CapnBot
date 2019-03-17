import discord
from discord.ext import commands
import random
import json 

class Duel(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def duel(self, ctx, user: discord.Member, bet:int):
        'Starts a duel with a user'
        if user == ctx.author:
            return await ctx.send("Silly you, you can't duel yourself!")
        data = await self.bot.db.fetchrow("SELECT * FROM users WHERE user_id = $1;",ctx.author.id)
        if data == None:
            return await ctx.send(f"Use {ctx.prefix}start to use this command")
        attacker_money = data["balance"]
        attacker_strength = data["strength"]
        data = await self.bot.db.fetchrow("SELECT * FROM users WHERE user_id = $1;",user.id)
        if data == None:
            return await ctx.send(f"This user hasn't set up a balance. They should use {ctx.prefix}start")
        defender_money = data["balance"]
        defender_strength = data["strength"]
        if attacker_money < bet:
            return await ctx.send("Not enough money for this bet.")
        elif defender_money < bet:
            return await ctx.send("That user doesn't have enough money for this bet.")
        await ctx.send(user.mention + "Do you accept the duel?")
        def check(message):
            return message.author == user and message.clean_content in ("y","n")
        response = await self.bot.wait_for('message',check = check, timeout=30)
        response = response.clean_content
        response = response.lower()
        if response == "y":
            attacker_damage = 0
            for i in range(attacker_strength):
                attacker_damage = attacker_damage + random.randint(1, 6)
            defender_damage = 0
            for i in range(defender_strength):
                defender_damage = defender_damage + random.randint(1, 6)
            await ctx.send(ctx.author.mention + " rolled a "+ str(attacker_damage))
            await ctx.send(user.mention + " rolled a " + str(defender_damage))
            if attacker_damage > defender_damage:
                await ctx.send((ctx.author.mention) + ' won the duel!')
                await ctx.send('Their strength has increased by one!')
                await ctx.send((('They have won $' + str(bet)) + ' from ') + user.name)
                attacker_money+=bet
                defender_money-=bet
                attacker_strength+=1
                defender_strength-=1
            elif attacker_damage == defender_damage:
                await ctx.send('It was a tie, nothing happens')
                return
            else:
                await ctx.send((user.mention) + ' won the duel!')
                await ctx.send('Their strength has increased by one!')
                await ctx.send((('They have won $' + str(bet)) + ' from ') + ctx.author.name)
                attacker_money-=bet
                defender_money+=bet
                attacker_strength-=1
                defender_strength+=1
            await self.bot.db.execute("UPDATE users SET balance=$1, strength=$2 WHERE user_id=$3",attacker_money,attacker_strength,ctx.author.id)
            await self.bot.db.execute("UPDATE users SET balance=$1, strength=$2 WHERE user_id=$3",defender_money,defender_strength,user.id)
        else:
            await ctx.send("Duel Declined")    
            

    @commands.command()
    async def strength(self, ctx,user :discord.Member= None):
        '''Shows your current strength'''
        if user == None:
            data = await self.bot.db.fetchrow("SELECT * FROM users WHERE user_id = $1;",ctx.author.id)
            if data == None:
                return await ctx.send(f"Use {ctx.prefix}start to use this command")
            attacker_strength = data["strength"]
            await ctx.send("Your strength is:"+str(attacker_strength))
        else:
            data = await self.bot.db.fetchrow("SELECT * FROM users WHERE user_id = $1;",user.id)
            if data == None:
                return await ctx.send(f"Use {ctx.prefix}start to use this command")
            attacker_strength = data["strength"]
            await ctx.send(user.name+"'s strength is: "+str(attacker_strength))

            
def setup(bot):
    bot.add_cog(Duel(bot))