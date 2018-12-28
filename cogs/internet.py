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
import asyncio
import time

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

    @commands.command(aliases=["ss","snap"])
    async def screenshot(self,ctx,website):
        headers = {"website": website}
        t1 = time.perf_counter()
        async with aiohttp.ClientSession() as ses:
            async with ses.post("https://magmachain.herokuapp.com/api/v1",headers = headers) as r:
                j = await r.json()
                try:
                    snap = j["snapshot"]
                except:
                    return await ctx.send("Invalid URL")
        t2 = time.perf_counter()
        t = round((t2-t1),2)
        e = discord.Embed(title = "Screenshot",url=j["website"], description="Took "+str(t)+ " seconds")
        e.set_image(url=snap)
        e.set_footer(text="Requested by "+ ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=e)

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

    @commands.command()
    async def lyrics(self,ctx,artist,*,song):
        art = artist.replace(" ", "%20")
        sng = song.replace(" ", "%20")
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://lyric-api.herokuapp.com/api/find/{art}/{sng}") as resp:
                response = await resp.json()
                if response["err"] == "not found":
                    return await ctx.send(f"The song {song} by {artist} was not found.")
                else:
                    lyrics = response["lyric"]
        if len(lyrics) < 500:
            blue = discord.Color.blue()
            em = discord.Embed(title="Song Lyrics",description=f"{song} by {artist}",color = blue)
            em.add_field(name="Lyrics:",value = lyrics)
            em.set_footer(text="Requested by "+ctx.author.name, icon_url= ctx.author.avatar_url)
            return await ctx.send(embed=em)
        lyrics = lyrics.split("\n")
        i = 0
        x=1
        lyric = lyrics[i*15:x*15]
        msg = ""
        for line in lyric:
            msg = msg + line + "\n"
        blue = discord.Color.blue()
        em = discord.Embed(title="Song Lyrics",description=f"{song} by {artist}",color = blue)
        em.add_field(name = "Lyrics",value = msg)
        em.set_footer(text="Requested by "+ctx.author.name, icon_url= ctx.author.avatar_url)
        message = await ctx.send(embed=em)
        await message.add_reaction("\U000025c0")
        await message.add_reaction("\U000025b6")
        await message.add_reaction("\U0001f6d1")
        times,remainder = divmod(len(lyrics),15)
        pages = times+1
        while True:
            def check(reaction, user):
                return user == ctx.author and reaction.emoji in ('\U000025c0', '\U000025b6','\U0001f6d1')
            try:
                reaction,user = await self.bot.wait_for("reaction_add",check=check,timeout=60)
            except asyncio.TimeoutError:
                break
            try:
                await message.remove_reaction(reaction.emoji,user)
            except:
                pass
            if reaction.emoji == '\U000025c0':
                if i == 0:
                    pass
                else:
                    i-=1
                    x-=1
            if reaction.emoji == '\U000025b6':
                if x == pages:
                    pass
                else:
                    i+=1
                    x+=1
            if reaction.emoji == '\U0001f6d1':
                return await message.delete()
            lyric = lyrics[i*15:x*15]
            msg = ""
            for line in lyric:
                msg = msg + line + "\n"
            em = discord.Embed(title="Song Lyrics",description=f"{song} by {artist}",color = blue)
            em.add_field(name = "Lyrics",value = msg )
            em.set_footer(text="Requested by "+ctx.author.name, icon_url= ctx.author.avatar_url)
            await message.edit(embed=em)
            
    @commands.command()
    async def trbmb(self,ctx):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.chew.pro/trbmb") as resp:
                text = await resp.text()
                text = text.strip('"[]')
                await ctx.send(text)

    @commands.command
    async def get_recipe(ctx, *, search):
        data = await self.bot.db.fetch("SELECT * FROM keys")
        app_id = data['recipe_id']
        app_key = data['recipe_key']
        async with aiohttp.ClientSession() as ses:
            async with ses.get("https://api.edamam.com/search?q="+search+"&app_id="+app_id+"&app_key="+app_key) as r:
                t = await r.json()
            await ses.close()
        if not t['hits']:
            return print("No Recipes Found")
        recipe = t['hits'][0]["recipe"]
        name = recipe['label']
        time = str(int(recipe['totalTime']))
        servings = str(int(recipe['yield']))
        url = recipe['shareAs']
        ingredients = "- " + "\n- ".join(recipe['ingredientLines'])
        diets = ", ".join(recipe['dietLabels'])
        health = ", ".join(recipe["healthLabels"])
        calories = str(int(recipe['calories']))
        nutrients = recipe['totalNutrients']
        nuts = []
        for entry in nutrients:
            e = nutrients[entry]
            nuts.append(e["label"]+" - " + str(round(e["quantity"],1)) + e["unit"])
        n = "\n".join(nuts)
        d = diets + ", " + health if diets else health 
        green = discord.Color.green()
        general = discord.Embed(title = name, description = "General Info", color = green, url = url)
        general.add_field(name= "Time to Make", value= time)
        general.add_field(name="Servings",value=servings)
        general.add_field(name= "Ingredients", value=ingredients)
        nutrition = discord.Embed(title = name, description="Nutrition Facts",url=url,color=green)
        nutrition.add_field(name="Health and Diet",value=d)
        nutrition.add_field(name="Calories", value=calories)
        nutrition.add_field(name="Contains", value = n)
        emojis = ("◀️","▶️","⏹")
        def check(reaction,user):
            return user == ctx.author and str(reaction.emoji) in emojis
        x = 0
        embeds = {0:general,1:nutrition}
        message = await ctx.send(embed=general)
        for emoji in emojis:
            await message.add_reaction(emoji)
        while True:
            try:
                r, u = self.bot.wait_for("reaction_add",check=check, timeout=60)
            except asyncio.TimeoutError:
                for emoji in emojis:
                    await message.remove_reaction(emoji)
                return
            else:
                if str(r.emoji) == "⏹":
                    return await message.delete()
                else:
                    if x == 0:
                        x = 1
                    else: 
                        x = 0
                em = embeds[x]
                message = await message.edit(embed = em)               
                

def setup(bot):
    bot.add_cog(Internet(bot))