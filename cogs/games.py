import discord
from discord.ext import commands
import random
import time
from discord.ext.commands.cooldowns import BucketType
import json
import aiohttp
import asyncpg


class Games():

    def __init__(self, bot):
        self.bot = bot
    @commands.command()
    async def trbmb(self,ctx):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.chew.pro/trbmb") as resp:
                text = await resp.text()
                text = text.strip('"[]')
                await ctx.send(text)

    @commands.command()
    async def start(self,ctx):
        data = await self.bot.db.fetchrow("SELECT * FROM users WHERE user_id=$1;", ctx.author.id)
        if data == None:
            now = int((int(time.time())-28800))
            await self.bot.db.execute("INSERT INTO users VALUES ($1, 100, $2, 10,False)", ctx.author.id, now)
            await ctx.send("You are now registered in the system")
        else:
            await ctx.send("User already in system")

    @commands.command()
    async def startuser(self,ctx, user: discord.Member):
        if not ctx.author.id == 422181415598161921:
            return
        data = await self.bot.db.fetchrow("SELECT * FROM users WHERE user_id=$1;",user.id)
        if data == None:
            now = int((int(time.time())-28800))
            await self.bot.db.execute("INSERT INTO users VALUES ($1, 100, $2, 10, False)",user.id, now)
            await ctx.send("Registered this user in the system")
        else:
            await ctx.send("User already in system")


    @commands.command()
    async def eightball(self, ctx):
        '-> Answers a question'
        answer = random.randint(1, 12)
        if answer == 1:
            line = 'Yes'
            await ctx.send(line)
        if answer == 2:
            line = 'No'
            await ctx.send(line)
        if answer == 3:
            line = 'Maybe'
            await ctx.send(line)
        if answer == 4:
            line = 'Possibly'
            await ctx.send(line)
        if answer == 5:
            line = 'Probably'
            await ctx.send(line)
        if answer == 6:
            line = 'Definitely'
            await ctx.send(line)
        if answer == 7:
            line = "I'm not sure, ask again"
            await ctx.send(line)
        if answer == 8:
            line = 'Probably Not'
            await ctx.send(line)
        if answer == 9:
            line = 'It is Likely'
            await ctx.send(line)
        if answer == 10:
            line = 'Definitely Not'
            await ctx.send(line)
        if answer == 11:
            line = 'It could work that way'
            await ctx.send(line)
        if answer == 12:
            line = 'Hopefully'
            await ctx.send(line)

    @commands.command()
    async def coinflip(self, ctx, side):
        '-> Flips a Coin'
        winner = random.randint(1, 200)
        if winner <= 100:
            winner = str(side).upper()
            await ctx.send('YOU WIN! IT WAS ' + winner)
        else:
            if str(side).lower() == 'heads':
                winner = 'tails'
            else:
                winner = 'heads'
            await ctx.send('Oh well, you lost. It was ' + winner)

    @commands.command()
    async def coin(self, ctx, bet:int):
        '-> 50/50 Gambling'
        winner = random.randint(1, 200)
        data = await self.bot.db.fetchrow("SELECT * FROM users WHERE user_id = $1;",ctx.author.id)
        if data == None:
            return await ctx.send(f"Use {ctx.prefix}start to use this command")
        balance = data["balance"]
        if balance < bet:
            return await ctx.send("You don't have enough money for this bet")
        if winner > 100:
            current = balance - bet
            await ctx.send('You lost. Balance is :$' + str(current))
        else:
            current = balance + bet
            await ctx.send('You won! Balance is :$' + str(current))
        await self.bot.db.execute("UPDATE users SET balance=$1 WHERE user_id=$2;",current,ctx.author.id)

    @commands.command(aliases = ["balance"])
    async def bal(self, ctx, user: discord.Member=None):
        "-> Shows User's Balance"
        if user == None:
            user = ctx.author
        balance = await self.bot.db.fetchrow("SELECT * FROM users WHERE user_ID=$1;",user.id)
        if balance == None:
            await self.bot.db.execute("INSERT INTO users VALUES ($1,100);",user.id)
            balance = 100
        else:
            balance = balance["balance"]
        await ctx.send(f"{user.name}'s balance is ${balance}")

    @commands.command()
    async def givemoney(self, ctx, user: discord.Member, amount: int):
        '-> Gives user Money'
        found = False
        if ((ctx.author.guild_permissions.administrator) or (ctx.author.id == 422181415598161921)):
            balance = await self.bot.db.fetchrow("SELECT * FROM users WHERE user_id=$1;",user.id)
            if balance == None:
                await self.bot.db.execute("INSERT INTO users (user_id, balance) VALUES ($1,100);",user.id)
                current = 100
            else:
                current = balance["balance"]
            now = current + amount
            await self.bot.db.execute("UPDATE users SET balance=$1 WHERE user_id=$2;",now,user.id)
            await ctx.send(f"{user.name}'s balance is now ${now}")
        else:
            await ctx.send('Permission Denied')

    @commands.command()
    async def rob(self, ctx, user: discord.Member):
        '-> Robs a User'
        if user == ctx.author:
            return await ctx.send("Silly you, you can't rob yourself!")
        now = time.time()
        data = await self.bot.db.fetchrow("SELECT * FROM users WHERE user_id = $1;",ctx.author.id)
        if data == None:
            return await ctx.send(f"Use {ctx.prefix}start to use this command")
        last_time = data["rob"]
        robbed_data = await self.bot.db.fetchrow("SELECT * FROM users WHERE user_id = $1;",user.id)
        if robbed_data == None:
            return await ctx.send(f"This user isn't registered. Tell them to use {ctx.prefix}start")
        if now - last_time < 28800:
            time_left = round(((28800-(now - last_time)) / 3600), 1)
            return await ctx.send(f"You still have {time_left} hours left before you can use this command")
        else:
            now = int(time.time())
            await self.bot.db.execute("UPDATE users SET rob=$1 WHERE user_id=$2",now,ctx.author.id)
        robbers_bal = data["balance"]
        robbed_bal = robbed_data["balance"]
        success = random.randint(0,10)
        if success <= 5:
            possible_money = (random.randint(0,robbed_bal) * 0.2)
            robbers_bal+=possible_money
            robbed_bal-=possible_money
            await ctx.send(f"You sneakily stole ${possible_money} from {user.name}")
        else:
            lost_money = (random.randint(0,robbers_bal) * 0.2)
            robbers_bal-=lost_money
            await ctx.send(f"You were caught and paid a fine of ${lost_money}")
        await self.bot.db.execute("UPDATE users SET balance=$1 WHERE user_id=$2",robbers_bal,ctx.author.id)
        await self.bot.db.execute("UPDATE users SET balance=$1 WHERE user_id=$2",robbed_bal,user.id)

        

    @commands.command()
    async def hangman(self, ctx, bet: int):
        '-> Plays Hangman'
        data = await self.bot.db.fetchrow("SELECT * FROM users WHERE user_id = $1;",ctx.author.id)
        if data == None:
            return await ctx.send(f"Use {ctx.prefix}start to use this command")
        users_money = data["balance"]
        if users_money < bet:
            return await ctx.send("You don't have enough money to make that bet")
        await ctx.send(('Hello, ' + ctx.author.mention) + ' Time to play hangman!')
        await ctx.send('HINT: The bot will only accept the first letter if you type more than one character')
        await ctx.channel.send(file=discord.File('cogs/Hangman Photos/1.PNG', filename='cogs/Hangman Photos/1.PNG'))
        word_list = ['hello', 'noodle', 'blank', 'loss', 'beetle', 'capn', 'trgcapn', 'what', 'super', 'bamboozle', 'beaned', 'lmao', 'scowled', 'smile', 'prank', 'shitty', 'logged', 'bot', 'package', 'user', 'lower', 'upper', 'medium', 'high', 'low', 'command']
        number = random.randint(0, 25)
        word = word_list[number]
        guesses = ''
        turns = 6
        img = 1
        while turns > 0:
            failed = 0
            text = ''
            for char in word:
                if char in guesses:
                    text = text + char
                else:
                    text = text + ' - '
                    failed = failed + 1
            await ctx.send(text)
            if failed == 0:
                await ctx.send('YOU WIN!!!')
                won = True
                break
            await ctx.send('Guess a character')
            try:
                def check(message):
                    return message.author == ctx.author
                guess = await self.bot.wait_for('message',check = check, timeout=30)
                guess = guess.clean_content
                guess = guess.lower()
            except AttributeError:
                await ctx.send("You didn't respond in time, game closed. The word was " + word)
                return
            guess = guess[0:1]
            if (not guess.isalpha()):
                await ctx.send("That's not a letter!")
                await ctx.send(('You have ' + str(turns)) + ' more guesses')
                if turns <= 0:
                    await ctx.send('You Lost.')
                    await ctx.send('The Word was :' + str(word))
                    won = False
                    break
            else:
                guesses = guesses + guess
                if guess not in word:
                    turns -= 1
                    img += 1
                    await ctx.send('Wrong')
                    await ctx.send(('You have ' + str(turns)) + ' more guesses')
                    await ctx.channel.send(file=discord.File(('cogs/Hangman Photos/' + str(img)) + '.PNG', filename=('cogs/Hangman Photos/' + str(img)) + '.PNG'))
                else:
                    await ctx.send('Correct!')
                    await ctx.channel.send(file=discord.File(('cogs/Hangman Photos/' + str(img)) + '.PNG', filename=('cogs/Hangman Photos/' + str(img)) + '.PNG'))
                if turns <= 0:
                    await ctx.send('You Lost. The word was ' + word)
                    won = False
                    break
        if won:
            current = users_money + bet
        else:
            current = users_money - bet
        await ctx.send("Your balance is now "+ str(current))
        await self.bot.db.execute("UPDATE users SET balance=$1 WHERE user_id=$2",current,ctx.author.id)



def setup(bot):
    bot.add_cog(Games(bot))