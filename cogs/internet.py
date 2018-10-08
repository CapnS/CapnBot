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
import asyncurban
import aiogoogletrans

c = CurrencyRates()
b = BtcConverter()
u = asyncurban.UrbanDictionary()
t = aiogoogletrans.Translator()

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
        data = await self.bot.db.fetchrow("SELECT * FROM keys;")
        api_key = data["api_key"]
        cse_id = data["cse_id"]
        '''Google search'''
        try:
            if ctx.channel.is_nsfw():
                safe = "off"
            else:
                safe = "high"
        except AttributeError:
            safe = "off"
        results = self.google(str(search), api_key, cse_id, num=1, safe = safe)
        for result in results:
            await ctx.send(result['link'])

    def google(self, search, key, _id, **kwargs):
        service = build('customsearch', 'v1', developerKey=key)
        res = service.cse().list(q=search, cx=_id, **kwargs).execute()
        return res['items']

    @commands.command(aliases=["image"])
    async def i(self,ctx,*,search):
        data = await self.bot.db.fetchrow("SELECT * FROM keys;")
        api_key = data["api_key"]
        cse_id = data["cse_id"]
        '''Image search for something'''
        try:
            if ctx.channel.is_nsfw():
                safe = "off"
            else:
                safe = "high"
        except AttributeError:
            safe = "high"
        results = self.google(str(search), api_key, cse_id, searchType = "image", num=1, safe = safe)
        for result in results:
            image = result["link"]
            await ctx.send(image)


    @commands.command()
    async def yt(self, ctx,*, search):
        '''Looks on youtube for something'''
        data = await self.bot.db.fetchrow("SELECT * FROM keys;")
        api_key = data["api_key"]
        url = "https://www.googleapis.com/youtube/v3/search"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params={"type": "video","q": search, "part": "snippet","key": api_key}) as resp:
                data = await resp.json()
        if data["items"]:
            video = data["items"][0]
            response = "https://youtu.be/" + video["id"]["videoId"]
        else:
            response = "This video was not found"
        await ctx.send(response)

    @commands.command()
    async def weather(self,ctx,*,city):
        '''gets weather data for a city'''
        replaced = city.replace(' ',"%20")
        data = await self.bot.db.fetchrow("SELECT * FROM keys;")
        key = data['weather_key']
        auth = {'Authorization':key}
        async with aiohttp.ClientSession(headers=auth) as session:
            async with session.get(f'http://api.openweathermap.org/data/2.5/weather?q={replaced}&units=imperial&appid={key}') as resp:
                text =await resp.json()
        weather = text['weather'][0]['main']
        icon = text['weather'][0]['icon']
        temp = text['main']['temp'] 
        humidity = text['main']['humidity']
        pressure = text['main']['pressure']
        wind = text['wind']['speed']
        clouds = text['clouds']['all']
        blue = discord.Color.blue()
        em = discord.Embed(title = "Weather Stats",description = city, color=blue)
        em.set_thumbnail(url =f'http://openweathermap.org/img/w/{icon}.png')
        em.set_footer(text="Requested by "+ ctx.author.name, icon_url= ctx.author.avatar_url)
        em.add_field(name="Forecast",value=weather)
        em.add_field(name="Temperature",value=f'{temp}°F')
        em.add_field(name='Humidity',value= f'{humidity}%')
        em.add_field(name="Pressure", value = f'{pressure}hPa')
        em.add_field(name="Wind Speed", value = f'{wind}mph')
        em.add_field(name="Cloud Cover",value = f'{clouds}% cloudy')
        await ctx.send(embed=em)

    @commands.group(invoke_without_command=True)
    async def ud(self, ctx):
        '-> Searches UD'
        await ctx.send("missing argument")
    
    @ud.command()
    async def random(self,ctx):
        word = await u.get_random()
        await ctx.send(f"{word} - {word.definition}")
    
    @ud.command()
    async def search(self,ctx,*,query):
        word = await u.get_word(query)
        await ctx.send(f"{word} - {word.definition}")

    @commands.command(aliases = ["gt", "trans"])
    async def translate(self,ctx,lang,*,sentence):
        data = await t.translate(sentence,dest=lang)
        translated = data.src.upper()
        translation = data.text
        language = lang.upper()
        green = discord.Color.green()
        em = discord.Embed(title = f"{translated} -> {language}",description=translation,color = green)
        em.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed = em)

def setup(bot):
    bot.add_cog(Internet(bot))