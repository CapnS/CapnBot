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
            uses = data["uses"]+1
            await self.bot.db.execute("UPDATE tags SET uses=$1 WHERE server_id=$2 AND name = $3;",uses,ctx.guild.id,search)
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
        await self.bot.db.execute("INSERT INTO tags VALUES ($1,$2,$3,$4,0);",ctx.guild.id,name,content,ctx.author.id)
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
        data = await self.bot.db.fetch("SELECT * FROM tags WHERE server_id=$1 AND owner_id=$2;",ctx.guild.id,ctx.author.id)
        entries = []
        for entry in data:
            entries.append(entry["name"])
        p = Pages(ctx,entries=entries,per_page=20)
        await p.paginate()

    @tag.command()
    async def claim(self,ctx,*,name):
        data = await self.bot.db.fetchrow("SELECT * FROM tags WHERE server_id=$1 AND name=$2;",ctx.guild.id,name)
        if not data:
            return await ctx.send("Tag doesn't exist")
        owner_id = data["owner_id"]
        owner = ctx.guild.get_member(owner_id)
        if owner:
            return await ctx.send("Owner still in server!")
        await self.bot.db.execute("UPDATE tags SET owner_id=$1 WHERE server_id=$2 AND name=$3;",ctx.author.id,ctx.guild.id,name)
        await ctx.send("Tag now belongs to you")

    @tag.command()
    async def info(self,ctx,*,name):
        data = await self.bot.db.fetchrow("SELECT * FROM tags WHERE server_id=$1 and name=$2;",ctx.guild.id,name)
        if not data:
            return await ctx.send("Tag not found")
        owner = ctx.guild.get_member(data["owner_id"])
        if not owner:
            mention = "None"
        else:
            mention = owner.mention
        uses = data["uses"]
        data = await self.bot.db.fetch("SELECT * FROM tags WHERE server_id=$1 ORDER BY uses DESC",ctx.guild.id)
        rank = 1
        for x in data:
            if x["name"] == name:
                break
            rank+=1
        blurple = discord.Color.blurple()
        em = discord.Embed(title = "Tag Information",description=name,color = blurple)
        em.add_field(name = "Owner",value= mention)
        em.add_field(name = "Uses",value = str(uses))
        em.add_field(name="Rank",value=str(rank))
        em.set_footer(text="Requested by "+ ctx.author.name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=em)

    @tag.command()
    async def all(self,ctx):
        data = await self.bot.db.fetch("SELECT * FROM tags WHERE server_id=$1;",ctx.guild.id)
        if not data:
            return await ctx.send("This server has no tags")
        entries = []
        for entry in data:
            entries.append(entry["name"])
        p = Pages(ctx,entries=entries,per_page=20)
        await p.paginate()        


def setup(bot):
    bot.add_cog(Tags(bot))