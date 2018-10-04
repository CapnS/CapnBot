import discord
from discord.ext import commands
import tweepy
from time import sleep
import time 
class Twitter():

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def follow(self, ctx, times):
        'Randomly follows'
        data = await self.bot.db.fetchrow("SELECT * FROM keys;")
        consumer_key = data["tweepy_key"]
        consumer_secret = data["tweepy_c_secret"]
        access_token = data["tweepy_token"]
        access_token_secret = data["tweepy_secret"]
        def go():
            message = ""
            auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
            auth.set_access_token(access_token, access_token_secret)
            api = tweepy.API(auth)
            amount = (- 1)
            for tweet in tweepy.Cursor(api.search, q='Fortnite').items():
                try:
                    amount = int(amount) + 1
                    if amount == int(times):
                        break
                    else:
                        sleep(5)
                except ValueError:
                    break
                try:
                    tweet.user.follow()
                    user_followed = tweet.user.name
                    message = message + user_followed + "\n"
                except tweepy.TweepError as e:
                    print(e.reason)
                except StopIteration:
                    break
                else:
                    sleep(5)
            return message
        if ctx.author.id == 422181415598161921:
            message = await self.bot.loop.run_in_executor(None,go)
            blue = discord.Color.blue()
            em = discord.Embed(title = "Followed Users",description = message,color = blue)
            await ctx.send(embed=em)
        else:
            return

    @commands.command()
    async def unfollow(self, ctx, people):
        'Unfollows People'
        data = await self.bot.db.fetchrow("SELECT * FROM keys;")
        consumer_key = data["tweepy_key"]
        consumer_secret = data["tweepy_c_secret"]
        access_token = data["tweepy_token"]
        access_token_secret = data["tweepy_secret"]
        def go():
            message = ""
            auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
            auth.set_access_token(access_token, access_token_secret)
            api = tweepy.API(auth)
            amount = (- 1)
            followers = api.followers_ids('TRGCapn')
            friends = api.friends_ids('TRGCapn')
            for f in friends:
                if f not in followers:
                    amount = int(amount) + 1
                    if amount == int(people):
                        break
                    else:
                        sleep(1)
                    user = str(api.get_user(f).screen_name)
                    api.destroy_friendship(f)
                    message = message + user + "\n"
            return message
        if ctx.author.id == 422181415598161921:
            message = await self.bot.loop.run_in_executor(None,go)
            blue = discord.Color.blue()
            em = discord.Embed(title = "Unfollowed Users",description = message,color = blue)
            await ctx.send(embed=em)
        else:
            return
    '''
    @commands.command()
    async def autofollow(self, ctx, minutes):
        'Autofollows people'
        data = await self.bot.db.fetchrow("SELECT * FROM keys;")
        consumer_key = data["tweepy_key"]
        consumer_secret = data["tweepy_c_secret"]
        access_token = data["tweepy_token"]
        access_token_secret = data["tweepy_secret"]
        if not ctx.author.id == 422181415598161921:
            return
        try:
            minutes = int(minutes)
        except ValueError:
            await ctx.send('Invalid time, please re-enter a number')
        await ctx.send(('Auto Following every ' + str(minutes)) + ' minute(s)')
        minutes = minutes * 60
        await ctx.send('You will have to exit the program to stop')
        await ctx.send('Are you sure you want to do this? (y/n)')
        answer = await self.bot.wait_for('message', timeout=30)
        if answer.clean_content == 'y':
            await ctx.send('Autofollowing')
        else:
            await ctx.send('Autofollow aborted')
            return
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth)
        try:
            for tweet in tweepy.Cursor(api.search, q='Fortnite').items():
                try:
                    tweet.user.follow()
                    try:
                        user_followed = tweet.user.name
                        await ctx.send('Followed ' + user_followed)
                    except UnicodeEncodeError:
                        await ctx.send('Error with name')
                    await asyncio.sleep(minutes)
                except tweepy.TweepError as e:
                    await ctx.send(e.reason)
                except StopIteration:
                    break
        except tweepy.TweepError as e:
            await ctx.send(e.reason)
    '''

    @commands.command()
    async def tweet(self, ctx,*, Message):
        'Tweets for me'
        data = await self.bot.db.fetchrow("SELECT * FROM keys;")
        consumer_key = data["tweepy_key"]
        consumer_secret = data["tweepy_c_secret"]
        access_token = data["tweepy_token"]
        access_token_secret = data["tweepy_secret"]
        if ctx.author.id == 422181415598161921:
            auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
            auth.set_access_token(access_token, access_token_secret)
            api = tweepy.API(auth)
            await ctx.send(('Do you want to tweet :' + str(Message)) + '? (y/n)')
            def check(message):
                return message.author == ctx.author
            answer = await self.bot.wait_for('message', check=check,timeout=30)
            if answer.clean_content == 'y':
                api.update_status(Message)
                await ctx.send('Tweeted: ' + Message)
            else:
                await ctx.send("Didn't Tweet")
        else:
            return

    @commands.command()
    async def retweet(self, ctx, search):
        'Retweets Something'
        data = await self.bot.db.fetchrow("SELECT * FROM keys;")
        consumer_key = data["tweepy_key"]
        consumer_secret = data["tweepy_c_secret"]
        access_token = data["tweepy_token"]
        access_token_secret = data["tweepy_secret"]
        if ctx.author.id == 422181415598161921:
            auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
            auth.set_access_token(access_token, access_token_secret)
            api = tweepy.API(auth)
            for tweet in api.search(str(search)):
                await ctx.send((str(tweet.user.name) + ' tweeted ') + str(tweet.text))
                await ctx.send('Do you want to retweet this? (y/n)')
                def check(message):
                    return message.author == ctx.author
                answer = await self.bot.wait_for('message', check = check,timeout=30)
                if answer.clean_content == 'y':
                    api.retweet(tweet.id)
                    await ctx.send(str(tweet.user.name) + ' was Retweeted!')
                else:
                    await ctx.send("Didn't Retweet")
                    return
                break
        else:
            await ctx.send('Insufficient Permissions')

def setup(bot):
    bot.add_cog(Twitter(bot))