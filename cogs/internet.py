import discord
from discord.ext import commands
from googleapiclient.discovery import build
import aiohttp
import urllib.parse
import urllib.request
import re
from forex_python.converter import CurrencyRates
from forex_python.bitcoin import BtcConverter
import sys



c = CurrencyRates()
b = BtcConverter()


class Internet():

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases= ["transfer"])
    async def currency(self, ctx, amount, currency1, currency2):
        '''Currency exchange'''
        try:
            amount = int(amount)
        except:
            return await ctx.send("Not a valid amount of money.")
        try:
            amount2 = round(c.convert(currency1,currency2,amount),2)
        except:
            return await ctx.send("Not a valid currency type")
        await ctx.send(f"{amount}{currency1} is {amount2}{currency2}")

    @commands.command(aliases = ["btc"])
    async def bitcoin(self,ctx, currency="USD"):
        try:
            amount = round(b.get_latest_price(currency),2)
        except:
            return await ctx.send("Not a valid currency type")
        await ctx.send(f'One BTC is {amount}{currency}')

    @commands.command(aliases=["tobtc"])
    async def moneytobtc(self,ctx,amount,currency):
        try:
            amount = int(amount)
        except:
            return await ctx.send("Not a valid amount of money")
        try:
            btc=round(b.convert_to_btc(amount,currency), 4)
        except:
            return await ctx.send("Not a valid currency")
        await ctx.send(f"{amount}{currency} is about {btc}BTC")

    @commands.command(aliases = ["google"])
    async def g(self, ctx,*, search):
        data = await db.fetchrow("SELECT * FROM keys;")
        api_key = data["api_key"]
        cse_id = data["cse_id"]
        '''Google search'''
        if ctx.channel.is_nsfw():
            safe = "off"
        else:
            safe = "high"
        results = self.google(str(search), api_key, cse_id, num=1, safe = safe)
        for result in results:
            await ctx.send(result['link'])

    def google(self, search, key, _id, **kwargs):
        service = build('customsearch', 'v1', developerKey=key)
        res = service.cse().list(q=search, cx=_id, **kwargs).execute()
        return res['items']

    @commands.command(aliases=["image"])
    async def i(self,ctx,*,search):
        data = await db.fetchrow("SELECT * FROM keys;")
        api_key = data["api_key"]
        cse_id = data["cse_id"]
        '''Image search for something'''
        if ctx.channel.is_nsfw():
            safe = "off"
        else:
            safe = "high"
        results = self.google(str(search), api_key, cse_id, searchType = "image", num=1, safe = safe)
        for result in results:
            image = result["link"]
            await ctx.send(image)


    @commands.command()
    async def yt(self, ctx,*, search):
        '''Looks on youtube for something'''
        query_string = urllib.parse.urlencode({
            'search_query': str(search),
        })
        html_content = urllib.request.urlopen('http://www.youtube.com/results?' + query_string)
        search_results = re.findall('href=\\"\\/watch\\?v=(.{11})', html_content.read().decode())
        await ctx.channel.send('http://www.youtube.com/watch?v=' + search_results[0])

def setup(bot):
    bot.add_cog(Internet(bot))