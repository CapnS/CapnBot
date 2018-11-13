import discord
from discord.ext import commands
import random
import time
from discord.ext.commands.cooldowns import BucketType
import json
import aiohttp
import asyncpg
from .paginator import Pages, CannotPaginate
from random import randint

class Player:
    def __init__(self):
        pass

    def get_move(self,grids):
        test_grids = grids
        player = 2
        n = 6
        x=0
        for grid in test_grids:
            i = 0
            for cell in grid:
                if cell == 0:
                    test_grids[x][i] = player
                    ai_will_win = self.check_if_won(test_grids,player,n)
                    if ai_will_win:
                        test_grids[x][i] = 0
                        return i+1
                    test_grids[x][i] = 0
                i+=1
            x+=1
        player = 1
        test_grids = grids
        x=0
        for grid in test_grids:
            i = 0
            for cell in grid:
                if cell == 0:
                    test_grids[x][i] = player
                    player_will_win = self.check_if_won(test_grids,player,n)
                    if player_will_win:
                        test_grids[x][i] = 0
                        return i+1
                    test_grids[x][i] = 0
                i+=1
            x+=1
        return randint(1,6)

    def check_if_won(self,grids,player,n):
        if self.horcheck_won(grids,player) or self.diagcheck_won(grids,player,n) or self.vertcheck_won(grids,player,n):
            return True

    def horcheck_won(self,grids, player):
        amount = 0
        for grid in grids:
            for cell in grid:
                if cell == player:
                    amount+=1
                    if amount >= 4:
                        return True
                else:
                    amount=0
            amount=0
        return False

    def vertcheck_won(self,grids,player,n):
        amount = 0
        for i in range(n):
            for grid in grids:
                if grid[i] == player:
                    amount+=1
                    if amount >= 4:
                        return True
                else:
                    amount = 0
            amount = 0
        return False

    def diagcheck_won(self, grids, player, n):
        for x in range(4):
            for y in range(3, 6):
                if grids[x][y] == player and grids[x+1][y-1] == player and grids[x+2][y-2] == player and grids[x+3][y-3] == player:
                    return True

        for x in range(4):
            for y in range(3):
                if grids[x][y] == player and grids[x+1][y+1] == player and grids[x+2][y+2] == player and grids[x+3][y+3] == player:
                    return True
                    
class Games():

    def __init__(self, bot):
        self.bot = bot
        self.Won = False
        

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

    @commands.command()
    async def connect4(self,ctx, user: discord.Member):
        n=6
        grids = [[0]*7 for _ in range(6)]
        green = discord.Color.green()
        msg = ""
        for x in grids:
            x = str(x)
            x = x.replace("0","⚪")
            msg = msg + x + "\n"
        em = discord.Embed(title="Current Board", description= msg,color = green)
        em.set_footer(text=f"{ctx.author}'s Turn")
        message = await ctx.send(embed = em)
        player = 1
        await self.domove(grids,player,n,message,ctx,user)
            
    async def check_if_won(self,grids,player,n,message,ctx,user):
        if self.horcheck_won(grids,player) or self.diagcheck_won(grids,player,n) or self.vertcheck_won(grids,player,n):
            if player == 1:
                mention = ctx.author
            else:
                mention = user
            await message.delete()
            blurple = discord.Color.blurple()
            msg = ""
            for x in grids:
                x = str(x)
                x = x.replace("0","⚪")
                x = x.replace("1", "⚫")
                x = x.replace("2", "🔴")
                msg = msg + x + "\n"
            em = discord.Embed(title="Current Board", description= msg,color = blurple)
            if player == 1:
                mention = ctx.author
            else:
                mention = user
            em.set_footer(text=f"{mention} won the Game")
            return await ctx.send(embed = em)
        await self.print_table(grids,message,ctx,player,user,n)


    async def domove(self,grids,player,n,message,ctx,user):
        move=0
        while not 0 < move <= 7:
            await ctx.send(f"Which coloumn do you want to place your checker in Player {player}(1-{7})")
            if player == 1:
                def check(message):
                    return message.author == ctx.author and message.clean_content.isdigit()
            else:
                def check(message):
                    return message.author == user and message.clean_content.isdigit()
            try:
                msg = await self.bot.wait_for('message',check = check,timeout=60)
            except:
                return
            msg = msg.clean_content
            try:
                move = int(msg)
            except ValueError:
                pass
        num=0
        for grid in grids:
            if num == 0:
                if grids[0][move-1] != 0:
                    await ctx.send("That column is full")
                    await self.domove(grids,player,n,message,ctx,user)
            if grid[move-1] == 0:
                if num == 5:
                    grids[num][move-1]=player
                else:
                    num+=1
            else:
                grids[num-1][move-1]=player
        await self.check_if_won(grids,player,n,message,ctx,user)
        
        
    async def print_table(self, grids,message,ctx,player,user,n):
        await message.delete()
        green = discord.Color.green()
        msg = ""
        for x in grids:
            x = str(x)
            x = x.replace("0","⚪")
            x = x.replace("1", "⚫")
            x = x.replace("2", "🔴")
            msg = msg + x +"\n"
        em = discord.Embed(title="Current Board", description= msg,color = green)
        if player == 2:
            mention = ctx.author
        else:
            mention = user
        em.set_footer(text=f"{mention}'s Turn")
        message=await ctx.send(embed = em)
        if not self.Won:
            if player == 1:
                player = 2
            else:
                player = 1
            await self.domove(grids,player,n,message,ctx,user)
        else:
            self.Won=False


    def horcheck_won(self,grids, player):
        amount = 0
        for grid in grids:
            for cell in grid:
                if cell == player:
                    amount+=1
                    if amount >= 4:
                        return True
                else:
                    amount=0
            amount=0
        return False

    def vertcheck_won(self,grids,player,n):
        amount = 0
        for i in range(7):
            for grid in grids:
                if grid[i] == player:
                    amount+=1
                    if amount >= 4:
                        return True
                else:
                    amount = 0
            amount = 0
        return False

    def diagcheck_won(self, grids, player, n):
        for x in range(4):
            for y in range(3, 6):
                if grids[x][y] == player and grids[x+1][y-1] == player and grids[x+2][y-2] == player and grids[x+3][y-3] == player:
                    return True

        for x in range(4):
            for y in range(6):
                if grids[x][y] == player and grids[x+1][y+1] == player and grids[x+2][y+2] == player and grids[x+3][y+3] == player:
                    return True

    @commands.command(aliases=["bj"])
    async def blackjack(self,ctx, bet:int):
        data = await self.bot.db.fetchrow("SELECT * FROM users WHERE user_id = $1;",ctx.author.id)
        if data == None:
            return await ctx.send(f"Use {ctx.prefix}start to use this command")
        users_money = data["balance"]
        if users_money < bet:
            return await ctx.send("You don't have enough money to make that bet")        
        dealer = []
        user = []
        for i in range(2):
            card = random.randint(1,13)
            if card >= 10:
                card = 10
            if card == 1:
                card = 11
            dealer.append(card)
            card = random.randint(1,13)
            if card >= 10:
                card = 10
            if card == 1:
                card = 11
            user.append(card)
        green = discord.Color.green()
        em = discord.Embed(title="Blackjack",description=ctx.author.name,color= green)
        em.add_field(name="Dealer",value = "["+str(dealer[0])+",?]")
        em.add_field(name=ctx.author.name,value=user)
        message = await ctx.send(embed = em)
        user_amount = 0
        dealer_amount = 0
        for x in user:
            user_amount+=x
        for x in dealer:
            dealer_amount+=x
        if user_amount == 21 and dealer_amount != 21:
            await message.delete()
            blue = discord.Color.blue()
            em = discord.Embed(title="Blackjack",description="BLACKJACK, You Win",color=blue)
            em.add_field(name="Dealer",value = dealer)
            em.add_field(name=ctx.author.name,value=user)
            return await ctx.send(embed = em)  
        while user_amount < 22:
            def check(message):
                return message.author == ctx.author and message.content in ("h","s")
            try:
                play = await self.bot.wait_for('message',check = check,timeout=60)
            except:
                return
            play = play.clean_content
            if play == "h":
                card = random.randint(1,13)
                if card >= 10:
                    card = 10
                if card == 1:
                    if user_amount + 11 <= 21:
                        card = 11
                user.append(card)
                user_amount+=card
                if user_amount > 21:
                    if 11 in user:
                        i = 0
                        for x in user:
                            if x == 11:
                                user.pop(i)
                                user.append(1)
                                user_amount-=10
                                break
                            i+=1
                    if user_amount > 21:
                        await message.delete()
                        red = discord.Color.red()
                        em = discord.Embed(title="Blackjack",description="Bust, Dealer Wins",color=red)
                        em.add_field(name="Dealer",value = str(dealer))
                        em.add_field(name=ctx.author.name,value=user)
                        current = users_money - bet
                        await self.bot.db.execute("UPDATE users SET balance=$1 WHERE user_id=$2",current,ctx.author.id)
                        return await ctx.send(embed = em)
                await message.delete()
                green = discord.Color.green()
                em = discord.Embed(title="Blackjack",description=ctx.author.name,color= green)
                em.add_field(name="Dealer",value = "["+str(dealer[0])+",?]")
                em.add_field(name=ctx.author.name,value=user)
                message = await ctx.send(embed = em)
            else:
                break
        if dealer_amount == 21:
            await message.delete()
            red = discord.Color.red()
            em = discord.Embed(title="Blackjack",description="Dealer has blackjack, You Lose",color=red)
            em.add_field(name="Dealer",value = dealer)
            em.add_field(name=ctx.author.name,value=user)
            current = users_money - bet
            await self.bot.db.execute("UPDATE users SET balance=$1 WHERE user_id=$2",current,ctx.author.id)
            return await ctx.send(embed = em)  
        while dealer_amount < 17:
            card = random.randint(1,13)
            if card >= 10:
                card = 10
            if card == 1:
                if dealer_amount + 11 <= 21:
                    card == 11
            dealer.append(card)
            dealer_amount+=card
            if dealer_amount > 21:
                i = 0
                if 11 in dealer:
                    for x in dealer:
                        if x == 11:
                            dealer.pop(i)
                            dealer.append(1)
                            dealer_amount-=10
                            break
                        i+=1
                if dealer_amount > 21:
                    await message.delete()
                    blue = discord.Color.blue()
                    em = discord.Embed(title="Blackjack",description="Dealer Busted, You Win",color=blue)
                    em.add_field(name="Dealer",value = dealer)
                    em.add_field(name=ctx.author.name,value=user)
                    current = users_money + bet
                    await self.bot.db.execute("UPDATE users SET balance=$1 WHERE user_id=$2",current,ctx.author.id)
                    return await ctx.send(embed = em)
            green = discord.Color.green()
            em = discord.Embed(title="Blackjack",description=ctx.author.name,color= green)
            em.add_field(name="Dealer",value = dealer)
            em.add_field(name=ctx.author.name,value=user)
            message = await ctx.send(embed = em)
        if dealer_amount > user_amount:
            await message.delete() 
            red = discord.Color.red()       
            em = discord.Embed(title="Blackjack",description="Dealer Wins",color=red)
            current = users_money - bet
            await self.bot.db.execute("UPDATE users SET balance=$1 WHERE user_id=$2",current,ctx.author.id)
        elif dealer_amount == user_amount:
            await message.delete()
            gold = discord.Color.gold()
            em = discord.Embed(title= "Blackjack",description = "It's a Draw",color = gold)
            current = users_money
        else:
            await message.delete()
            blue = discord.Color.blue()
            em = discord.Embed(title="Blackjack",description="You win!",color=blue)
            current = users_money + bet
            await self.bot.db.execute("UPDATE users SET balance=$1 WHERE user_id=$2",current,ctx.author.id)
        em.add_field(name="Dealer",value = dealer)
        em.add_field(name=ctx.author.name,value=user)
        await ctx.send(embed = em)
        await ctx.send("Your new balance is $"+str(current)) 

            
    @commands.command(aliases=["lb","top"])
    async def leaderboard(self,ctx):
        data = await self.bot.db.fetch("SELECT user_id,balance FROM users ORDER BY balance DESC;")
        balances = []
        for x in data:
            user = await self.bot.get_user_info(x["user_id"])
            balance = x["balance"]
            balances.append(f"{user.name} - ${balance}")
        p = Pages(ctx,entries=balances)
        await p.paginate()

    @commands.command()
    async def aiconnect4(self,ctx):
        n=7
        grids = [[0]*7 for _ in range(6)]
        player = 1
        msg = ""
        for x in grids:
            x = str(x)
            x = x.replace("0","⚪")
            msg = msg + x + "\n"
        green = discord.Color.green()
        em = discord.Embed(title="Current Board", description= msg,color = green)
        em.set_footer(text=f"{ctx.author}'s Turn")
        message = await ctx.send(embed = em)
        user = "AI"
        await self.ai_domove(grids,player,n,ctx,message,user)

    async def ai_domove(self,grids,player,n,ctx,message,user):
        ai = Player()
        move=0
        while not 0 < move <= 7:
            if player == 1:
                await ctx.send(f"Which coloumn do you want to place your checker in Player {player}(1-{7})")
                def check(message):
                    return message.author == ctx.author and message.clean_content.isdigit()
                try:
                    msg = await self.bot.wait_for('message',check = check,timeout=60)
                except:
                    pass
                msg = msg.clean_content
                try:
                    move = int(msg)
                except ValueError:
                    pass
            else:
                move = ai.get_move(grids)
        num=0
        for grid in grids:
            if num == 0:
                if grids[0][move-1] != 0:
                    await ctx.send("That column is full")
                    await self.ai_domove(grids,player,n,ctx,message,user)
            if grid[move-1] == 0:
                if num == 5:
                    grids[num][move-1]=player
                else:
                    num+=1
            else:
                grids[num-1][move-1]=player
        await self.ai_check_if_won(grids,player,n,message,ctx,user)
        
    async def ai_check_if_won(self,grids,player,n,message,ctx,user):
        if self.horcheck_won(grids,player) or self.diagcheck_won(grids,player,n) or self.vertcheck_won(grids,player,n):
            if player == 1:
                mention = ctx.author
            else:
                mention = user
            await message.delete()
            blurple = discord.Color.blurple()
            msg = ""
            for x in grids:
                x = str(x)
                x = x.replace("0","⚪")
                x = x.replace("1", "⚫")
                x = x.replace("2", "🔴")
                msg = msg + x + "\n"
            em = discord.Embed(title="Current Board", description= msg,color = blurple)
            if player == 1:
                mention = ctx.author
            else:
                mention = user
            em.set_footer(text=f"{mention} won the Game")
            return await ctx.send(embed = em)
        await self.ai_print_table(grids,message,ctx,player,user,n)

    async def ai_print_table(self, grids, message,ctx,player,user,n):
        await message.delete()
        if player == 2:
            await self.ai_domove(grids,player,n,ctx,message,user)
            return
        green = discord.Color.green()
        msg = ""
        for x in grids:
            x = str(x)
            x = x.replace("0","⚪")
            x = x.replace("1", "⚫")
            x = x.replace("2", "🔴")
            msg = msg + x +"\n"
        em = discord.Embed(title="Current Board", description= msg,color = green)
        if player == 2:
            mention = ctx.author
        else:
            mention = user
        em.set_footer(text=f"{mention}'s Turn")
        message=await ctx.send(embed = em)
        if not self.Won:
            if player == 1:
                player = 2
            else:
                player = 1
            await self.ai_domove(grids,player,n,ctx,message,user)
        else:
            self.Won=False
    
def setup(bot):
    bot.add_cog(Games(bot))