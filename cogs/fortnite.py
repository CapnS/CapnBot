import discord
from discord.ext import commands
import aiohttp


class Fortnite(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def fortnite(self,ctx,platform,*,user):
        '''Gets fortnite stats of a user from a specific platform'''
        data = await self.bot.db.fetchrow("SELECT * from keys;")
        ft= data["fortnite_token"]
        authorization = {'Authorization':ft}
        async with aiohttp.ClientSession(headers=authorization) as session:
            payload = {'username':user}
            async with session.post('https://fortnite-public-api.theapinetwork.com/prod09/users/id',data = payload) as resp:
                text=await resp.json()
                user_id= text.get('uid')
            if user_id == None:
                return await ctx.send("Not an Epic Games User.")
            payload = {'user_id': user_id, 'platform': platform, 'window' : "alltime"}
            async with session.post('https://fortnite-public-api.theapinetwork.com/prod09/users/public/br_stats',data=payload) as resp:
                text = await resp.json()
                error = text.get("error")
                if error:
                    return await ctx.send("This user doesn't play on this Platform")
                stats = text.get("stats")
                total = text.get("totals")
                green = discord.Color.green()
                em = discord.Embed(title="Fortnite Stats",description = user,color =green)
                em.add_field(name="Solo Wins",value = stats.get("placetop1_solo"))
                em.add_field(name="Duo Wins",value = stats.get("placetop1_duo"))
                em.add_field(name="Squad Wins",value = stats.get("placetop1_squad"))
                em.add_field(name= "Total Wins",value = total.get("wins"))
                em.add_field(name = "Win Ratio",value = f"{total.get('winrate')}%")
                em.add_field(name="Total Score", value = total.get("score"))
                em.add_field(name = "Kills", value = total.get("kills"))
                em.add_field(name="Matches Played",value = total.get("matchesplayed"))
                em.add_field(name = "K/D", value = total.get("kd"))
                em.set_footer(text="Requested by "+ctx.author.name,icon_url=ctx.author.avatar_url)
                await ctx.send(embed=em)
    
    @commands.command()
    async def fnchallenges(self,ctx):
        data = await self.bot.db.fetchrow("SELECT * from keys;")
        ft= data["fortnite_token"]
        authorization = {'Authorization':ft,'X-Fortnite-API-Version':'v1.1'}
        async with aiohttp.ClientSession(headers=authorization) as session:
            payload = {"season" : "current","language":"en"}
            async with session.post('https://fortnite-public-api.theapinetwork.com/prod09/challenges/get',data=payload) as resp:
                text = await resp.json()
                msg = ""
                current = text.get("currentweek")
                all_challenges = text.get("challenges")
                weekly_challenges = all_challenges[current-1]
                challenges = weekly_challenges.get("entries")
                for entry in challenges:
                    challenge = entry.get("challenge")
                    total = entry.get("total")
                    stars = entry.get("stars")
                    msg = f"{msg} \n {challenge} - 0/{total} - {stars} stars"
                green = discord.Color.green()
                em = discord.Embed(title="Battle Royale Challenges",description = msg, color = green)
                em.set_footer(text="Requested by "+ctx.author.name,icon_url=ctx.author.avatar_url)
                await ctx.send(embed = em)



    '''
    @commands.command()
    async def fnstore(self,ctx):
        data = await self.bot.db.fetchrow("SELECT * from keys;")
        ft= data["fortnite_token"]
        authorization = {'Authorization':ft}
        async with aiohttp.ClientSession(headers=authorization) as session:
            payload = {"language":"en"}
            async with session.post('https://fortnite-public-api.theapinetwork.com/prod09/store/get',data=payload) as resp:
                print(await resp.json())
    '''
def setup(bot):
    bot.add_cog(Fortnite(bot))