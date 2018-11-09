import discord
from discord.ext import commands
import difflib
from .paginator import Pages, CannotPaginate
import datetime
import re

class Tags():
    def __init__(self,bot):
        self.bot = bot


    
    @commands.group(invoke_without_command=True)
    async def tag(self,ctx,*,search):
        '''responds with a tag'''
        data = await self.bot.db.fetchrow("SELECT * FROM tags WHERE server_id=$1 AND name=$2;",ctx.guild.id,search)
        if data:
            uses = data["uses"]+1
            await self.bot.db.execute("UPDATE tags SET uses=$1 WHERE server_id=$2 AND name = $3;",uses,ctx.guild.id,search)
            content = data["content"]
            regex = r"{(?:ctx\.([\w\.]+))}+"
            def tag_replace(match):
                full_match = match.group(0)
                result = match.group(1)
                subject = ctx
                attrs = result.split('.')
                if attrs[0] not in ['author', 'channel','message']:
                    return full_match
                try:
                    for attr in attrs:
                        if attr.startswith('_'):
                            return full_match
                        subject = getattr(subject, attr)
                except AttributeError:
                    return full_match
                finally:
                    return str(subject)
            new_str = re.sub(regex, tag_replace, content, re.MULTILINE)
            return await ctx.send(new_str)
        data = await self.bot.db.fetch("SELECT * FROM tags WHERE server_id=$1 AND name % $2 ORDER BY similarity(name,$2) DESC LIMIT 3;",ctx.guild.id,search)
        msg = ""
        for match in data:
            msg = msg + match["name"] + "\n"
        await ctx.send("This tag doesn't exist, try these instead: \n" + msg)

    @tag.command()
    async def alias(self,ctx,name,*,new_name):
        data = await self.bot.db.fetch("SELECT * from tags WHERE server_id=$1 AND name=$2;",ctx.guild.id,new_name)
        if data:
            return await ctx.send("A tag or alias with that name already exists")
        data = await self.bot.db.fetchrow("SELECT * from tags WHERE server_id=$1 AND name=$2;",ctx.guild.id,name)
        if not data:
            return await ctx.send("Tag "+ name + " doesn't exist")
        content = data["content"]
        now = str(datetime.datetime.utcnow())
        await self.bot.db.execute("INSERT INTO tags VALUES ($1,$2,$3,$4,0,$5,$6);",ctx.guild.id,new_name,content,ctx.author.id,now,name)
        await ctx.send(f"Alias {new_name} has been created")        

    @tag.command()
    async def create(self,ctx,name,*,content):
        '''creates a tag'''
        data = await self.bot.db.fetch("SELECT * from tags WHERE server_id=$1 AND name=$2;",ctx.guild.id,name)
        if data:
            return await ctx.send("A tag or alias with that name already exists")
        now = str(datetime.datetime.utcnow())
        await self.bot.db.execute("INSERT INTO tags VALUES ($1,$2,$3,$4,0,$5,'None');",ctx.guild.id,name,content,ctx.author.id,now)
        await ctx.send(f"Tag {name} has been created")

    @tag.command()
    async def delete(self,ctx,*,name):
        '''deletes a tag you own'''
        data = await self.bot.db.fetch("SELECT * from tags WHERE server_id=$1 AND name=$2 AND owner_id=$3;",ctx.guild.id,name,ctx.author.id)
        if data:
            await self.bot.db.execute("DELETE FROM tags WHERE server_id=$1 AND name=$2 AND owner_id=$3;",ctx.guild.id,name,ctx.author.id)
            return await ctx.send("Tag deleted")
        await ctx.send("Tag either doesn't belong to you or doesn't exist")

    @tag.command()
    async def edit(self,ctx,name,*,content):
        '''edits a tag you own'''
        data = await self.bot.db.fetch("SELECT * from tags WHERE server_id=$1 AND name=$2 AND owner_id=$3;",ctx.guild.id,name,ctx.author.id)
        if data:
            await self.bot.db.execute("UPDATE tags SET content=$4 WHERE server_id=$1 AND name=$2 AND owner_id=$3;",ctx.guild.id,name,ctx.author.id,content)
            return await ctx.send("Tag edited")
        await ctx.send("Tag either doesn't belong to you or doesn't exist")

    @tag.command()
    async def search(self,ctx,*,search):
        '''searches for a tag'''
        data = await self.bot.db.fetch("SELECT * FROM tags WHERE server_id=$1 and name % $2 ORDER BY similarity(name,$2) DESC LIMIT 50;",ctx.guild.id,search)
        entries = []
        for row in data:
            entries.append(row["name"])
        p = Pages(ctx,entries=entries,per_page=10)
        await p.paginate()

    @commands.command()
    async def tags(self,ctx):
        '''shows all your tags in a server'''
        data = await self.bot.db.fetch("SELECT * FROM tags WHERE server_id=$1 AND owner_id=$2;",ctx.guild.id,ctx.author.id)
        entries = []
        for entry in data:
            entries.append(entry["name"])
        if len(entries) == 0:
            return await ctx.send("You have no tags")
        p = Pages(ctx,entries=entries,per_page=20)
        await p.paginate()

    @tag.command()
    async def claim(self,ctx,*,name):
        '''claims an unowned tag'''
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
        '''gets info on a command'''
        data = await self.bot.db.fetchrow("SELECT * FROM tags WHERE server_id=$1 and name=$2;",ctx.guild.id,name)
        if not data:
            return await ctx.send("Tag not found")
        owner = ctx.guild.get_member(data["owner_id"])
        if not owner:
            mention = "None"
        else:
            mention = owner.mention
        uses = data["uses"]
        timestamp = data["created"]
        alias = data["alias"]
        data = await self.bot.db.fetch("SELECT * FROM tags WHERE server_id=$1 ORDER BY uses DESC",ctx.guild.id)
        rank = 1
        for x in data:
            if x["name"] == name:
                break
            rank+=1
        timestamp = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
        blurple = discord.Color.blurple()
        if not alias == "None":
            em = discord.Embed(title = "Alias Information",description=name,color = blurple, timestamp=timestamp)
            em.add_field(name="Owner", value = mention)
            em.add_field(name = "Original",value = alias)
            em.set_footer(text = "Alias was Created")
            return await ctx.send(embed= em)
        em = discord.Embed(title = "Tag Information",description=name,color = blurple, timestamp=timestamp)
        em.add_field(name = "Owner",value= mention)
        em.add_field(name = "Uses",value = str(uses))
        em.add_field(name="Rank",value=str(rank))
        em.set_footer(text="Tag was Created")
        await ctx.send(embed=em)

    @tag.command()
    async def all(self,ctx):
        ''' shows all tags for a server'''
        data = await self.bot.db.fetch("SELECT * FROM tags WHERE server_id=$1;",ctx.guild.id)
        if not data:
            return await ctx.send("This server has no tags")
        entries = []
        for entry in data:
            entries.append(entry["name"])
        p = Pages(ctx,entries=entries,per_page=20)
        await p.paginate()        

    @tag.command()
    async def raw(self,ctx,*,name):
        data = await self.bot.db.fetchrow("SELECT * FROM tags WHERE server_id=$1 AND name=$2;",ctx.guild.id,name)
        if not data:
            return await ctx.send("Tag "+ name + " wasn't found")
        content = data["content"]
        transformations = {
            re.escape(c): '\\' + c
            for c in ('*', '`', '_', '~', '\\', '<')
        }
        def replace(obj):
            return transformations.get(re.escape(obj.group(0)), '')

        pattern = re.compile('|'.join(transformations.keys()))
        await ctx.send(pattern.sub(replace, content))

def setup(bot):
    bot.add_cog(Tags(bot))