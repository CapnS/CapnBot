import discord
from discord.ext import commands

class CapnChat():
    def __init__(self,bot):
        self.bot = bot

    @commands.command()
    async def cb(self,ctx,*,statement):
        data = await self.bot.db.fetchrow("SELECT * FROM keys;")
        key = data["travitia"]
        if not (3 <= len(statement) <= 60):
            return await ctx.send("Text must be longer than 3 chars and shorter than 60.")
        payload = {"text": statement}
        async with ctx.channel.typing(), ctx.bot.session.post("https://public-api.travitia.xyz/talk", json=payload, headers={"authorization": key}) as req:
            await ctx.send((await req.json())["response"])



def setup(bot):
    bot.add_cog(CapnChat(bot))