import discord
from discord.ext import commands
import twitchio
import aiohttp
import datetime


class Twitch():
    def __init__(self,bot):
        self.bot = bot
        
    
    @commands.command()
    async def stream(self,ctx,name):
        data = await self.bot.db.fetchrow("SELECT * FROM keys;")
        twitch_id = data["twitch_oauth"]
        t = twitchio.client.TwitchClient(client_id=twitch_id,loop=self.bot.loop)
        stream = await t.get_stream_by_name(name)
        data = stream["data"]
        if data:
            data = data[0]
            title = data["title"]
            viewers = data["viewer_count"]
            started = data["started_at"][11:19]
            game_id = data["game_id"]
            url = data["thumbnail_url"]
            url = url.replace("width","1920")
            url = url.replace("height","1080")
            url = url.replace("{","")
            url = url.replace("}","")
            print(url)
            auth = {"Client-ID": twitch_id}
            async with aiohttp.ClientSession(headers=auth) as session:
                async with session.get("https://api.twitch.tv/helix/games?id="+str(game_id)) as resp:
                    data = await resp.json()
                    data = data["data"]
                    data = data[0]
                    game = data["name"]
            red = discord.Color.red()
            em = discord.Embed(title = "Stream Stats", description=name,color =red)
            em.add_field(name="Title",value=title)
            em.add_field(name= "Game",value = game)
            em.add_field(name="Viewer Count",value=viewers)
            em.add_field(name="Started At",value = started)
            em.add_field(name = "Link", value= f"[Twitch](https://twitch.tv/{name})")
            em.set_thumbnail(url=url)
            return await ctx.send(embed=em)
        else:
            return await ctx.send("User is not Streaming")
            
        print(stream)

def setup(bot):
    bot.add_cog(Twitch(bot))