import discord
from discord.ext import commands
import difflib
from .paginator import Pages, CannotPaginate

class Tags():
    def __init__(self,bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def tag(self,ctx,*,search):
        data = await self.bot.db.fetchrow("SELECT * FROM tags WHERE server_id=$1 AND name=$2;",ctx.guild.id,search)
        if data:
            return await ctx.send(data["content"])
        data = await self.bot.db.fetch("SELECT * FROM tags WHERE server_id=$1 AND name % $2 ORDER BY similarity(name,$2) DESC LIMIT 3;",ctx.guild.id,search)
        msg = ""
        for match in data:
            msg = msg + match["name"] + "\n"
        await ctx.send("This tag doesn't exist, try these instead: \n" + msg)


    @tag.command()
    async def create(self,ctx,name,*,content):
        data = await self.bot.db.fetch("SELECT * from tags WHERE server_id=$1 AND name=$2;",ctx.guild.id,name)
        if data:
            return await ctx.send("A tag with that name already exists")
        await self.bot.db.execute("INSERT INTO tags VALUES ($1,$2,$3,$4);",ctx.guild.id,name,content,ctx.author.id)
        await ctx.send(f"Tag {name} has been created")

    @tag.command()
    async def delete(self,ctx,*,name):
        data = await self.bot.db.fetch("SELECT * from tags WHERE server_id=$1 AND name=$2 AND owner_id=$3;",ctx.guild.id,name,ctx.author.id)
        if data:
            await self.bot.db.execute("DELETE FROM tags WHERE server_id=$1 AND name=$2 AND owner_id=$3;",ctx.guild.id,name,ctx.author.id)
            return await ctx.send("Tag deleted")
        await ctx.send("Tag either doesn't belong to you or doesn't exist")

    @tag.command()
    async def edit(self,ctx,name,*,content):
        data = await self.bot.db.fetch("SELECT * from tags WHERE server_id=$1 AND name=$2 AND owner_id=$3;",ctx.guild.id,name,ctx.author.id)
        if data:
            await self.bot.db.execute("UPDATE tags SET content=$4 WHERE server_id=$1 AND name=$2 AND owner_id=$3;",ctx.guild.id,name,ctx.author.id,content)
            return await ctx.send("Tag edited")
        await ctx.send("Tag either doesn't belong to you or doesn't exist")

    @tag.command()
    async def search(self,ctx,*,search):
        data = await self.bot.db.fetch("SELECT * FROM tags WHERE server_id=$1 and name % $2 ORDER BY similarity(name,$2) DESC LIMIT 50;",ctx.guild.id,search)
        entries = []
        for row in data:
            entries.append(row["name"])
        p = Pages(ctx,entries=entries,per_page=10)
        await p.paginate()

    @commands.command()
    async def tags(self,ctx):
        data = await self.bot.db.fetch("SELECT * FROM tags WHERE server_id=$1 AND owner_id=$2",ctx.guild.id,ctx.author.id)
        entries = []
        for entry in data:
            entries.append(entry["name"])
        p = Pages(ctx,entries=entries,per_page=20)
        await p.paginate()



def setup(bot):
    bot.add_cog(Tags(bot))