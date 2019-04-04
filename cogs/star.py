# -*- coding: utf-8 -*-

from discord.ext import commands
import discord

class Star(commands.Cog):
    """Starboard commands"""

    def __init__(self, bot):
        self.bot = bot
    
    def get_star(self, count):
        if count < 5:
            return ":star:"
        elif count < 10:
            return ":star2:"
        elif count < 25:
            return ":dizzy:"
        else:
            return ":sparkles:"

    async def get_starboard_channel(self, guild_id, needed=False):
        channel = await self.bot.db.fetchrow("SELECT * FROM star_channels WHERE guild_id=$1", guild_id)
        if not channel:
            if needed:
                return False, False
            else:
                return False
        else:
            if needed:
                return channel["channel_id"], channel["needed"]
            else:
                return channel["channel_id"]

    async def delete_starboard(self, ctx):
        starboard_channel = await self.get_starboard_channel(ctx.guild.id)
        if not starboard_channel:
            return await ctx.send("You don't have a starboard setup, ask an admin to set one up for this guild.")
        await self.bot.db.execute("DELETE FROM star_channels WHERE guild_id=$1", ctx.guild.id)
        await self.bot.db.execute("DELETE FROM starboard WHERE channel_id=$1", starboard_channel)
        await self.bot.db.execute("DELETE FROM givers WHERE guild_id=$1", ctx.guild.id)

    async def update_starrers(self, starrers, message_id, starboard_message_id=None):
        await self.bot.db.execute("UPDATE starrers SET starrers=$1 WHERE message_id=$2 or message_id=$3", starrers, message_id, starboard_message_id)
   
    async def star_message(self, *, channel_id, message_id, user_id, guild_id, ctx=None):
        try:
            user = self.bot.get_user(user_id)
            if user.bot:
                return
            starboard_channel, needed = await self.get_starboard_channel(guild_id, True)
            if not starboard_channel:
                return await ctx.send("You don't have a starboard setup, ask an admin to set one up for this guild.")
            else:
                current_channel = self.bot.get_channel(channel_id)
                star_channel = self.bot.get_channel(starboard_channel)
                if current_channel.is_nsfw() and not star_channel.is_nsfw():
                    return await ctx.send("You can't star in an NSFW channel if your starboard isn't NSFW.")
            starrers = await self.bot.db.fetchrow("SELECT * FROM starrers WHERE message_id=$1", message_id)
            if not starrers:
                starboard_data = await self.bot.db.fetchrow("SELECT * FROM starboard WHERE starboard_message_id=$1", message_id)
                if starboard_data:
                    starrers = await self.bot.db.fetchrow("SELECT * FROM starrers WHERE message_id=$1", starboard_data["original_message_id"])
                    if starrers:
                        old_starrers = starrers["starrers"]
                        if user_id in old_starrers:
                            return await ctx.send("You've already starred that message")
            else:
                old_starrers = starrers["starrers"]
                if user_id in old_starrers:
                    return await ctx.send("You've already starred that message")
            try:
                old_starrers.append(user_id)
                new_starrers = old_starrers
            except NameError:
                try:
                    c = self.bot.get_channel(channel_id)
                    m = await c.fetch_message(message_id)
                except:
                    c = self.bot.get_channel(starboard_channel)
                    try:
                        m = await c.fetch_message(message_id)
                    except:
                        return await ctx.send("That message was not sent in this channel or in the starboard channel.")
                if m.author.id == user_id:
                    return await ctx.send("You can't star your own message.")
                new_starrers = [user_id]
                if needed != 1:
                    await self.bot.db.execute("INSERT INTO starrers VALUES ($1, $2)", message_id, new_starrers)
                    await self.bot.db.execute("INSERT INTO givers VALUES ($1, $2, $3)", user_id, guild_id, message_id)
                    return await ctx.send("Starred the message.")
            if len(new_starrers) < needed:
                await self.update_starrers(new_starrers, message_id)
                await self.bot.db.execute("INSERT INTO givers VALUES ($1, $2, $3)", user_id, guild_id, message_id)
                return await ctx.send("Message Starred.")
            message_data = await self.bot.db.fetchrow("SELECT * FROM starboard WHERE original_message_id=$1 or starboard_message_id=$1", message_id)
            if not message_data:
                c = self.bot.get_channel(channel_id)
                m = await c.fetch_message(message_id)
                if m.author.id == user_id:
                    return await ctx.send("You can't star your own message")
                gold = discord.Color.gold()
                em = discord.Embed(description=m.content, color=gold)
                if m.embeds:
                    data = m.embeds[0]
                    if data.type == 'image':
                        em.set_image(url=data.url)
                if m.attachments:
                    file = m.attachments[0]
                    if file.url.lower().endswith(('png', 'jpeg', 'jpg', 'gif', 'webp')):
                        em.set_image(url=file.url)
                    else:
                        em.add_field(name='Attachment', value='['+file.filename+']('+file.url+')', inline=False)
                em.add_field(name='Message', value='[Message Link]('+m.jump_url+')', inline=False)
                em.set_author(name=m.author.name, icon_url=m.author.avatar_url)
                em.timestamp = m.created_at
                channel = self.bot.get_channel(starboard_channel)
                count = len(new_starrers)
                star = self.get_star(count)
                content = star+str(count)+ " | "+c.mention
                message = await channel.send(content, embed=em)
                await self.update_starrers(new_starrers, message_id)
                await self.bot.db.execute("INSERT INTO starboard VALUES($1, $2, $3, $4, $5)", message_id, message.id, channel.id, count, m.author.id)
                await self.bot.db.execute("INSERT INTO givers VALUES ($1, $2, $3)", user_id, guild_id, message_id)
                return await ctx.send("Message Starred")
            if user_id == message_data["author_id"]:
                return await ctx.send("You can't star your own message.")
            c = self.bot.get_channel(message_data["channel_id"])
            if not c:
                await self.bot.db.execute("DELETE FROM star_channels WHERE channel_id=$1", starboard_channel)
                await self.bot.db.execute("DELETE FROM starboard WHERE channel_id=$1", starboard_channel)
                return await ctx.send("The starboard channel for this guild was not found.")
            try:
                message = await c.fetch_message(message_data["starboard_message_id"])
            except:
                await self.bot.db.execute("DELETE FROM starboard WHERE starboard_message_id=$1", message_data["starboard_message_id"])
                return
            em = message.embeds[0]
            count = len(new_starrers)
            star = self.get_star(count)
            content = star+str(count)+ " | " + message.content.split(" | ")[1]
            await message.edit(content=content, embed=em)
            await self.bot.db.execute("UPDATE starboard SET stars=$1 WHERE starboard_message_id=$2", count, message_data["starboard_message_id"])
            await self.update_starrers(new_starrers, message_id)
            await self.bot.db.execute("INSERT INTO givers VALUES ($1, $2, $3)", user_id, guild_id, message_id)
            await ctx.send("Message Starred.")
        except AttributeError:
            pass

    async def unstar_message(self, *, channel_id, message_id, user_id, guild_id, ctx=None):
        try:
            user = self.bot.get_user(user_id)
            if user.bot:
                return
            starboard_channel, needed = await self.get_starboard_channel(guild_id, True)
            if not starboard_channel:
                return await ctx.send("This guild does not have a starboard channel set up.")
            starrers = await self.bot.db.fetchrow("SELECT * FROM starrers WHERE message_id=$1", message_id)
            starboard_message = None
            if not starrers:
                starboard_data = await self.bot.db.fetchrow("SELECT * FROM starboard WHERE starboard_message_id=$1", message_id)
                if starboard_data:
                    star_message = starboard_data["original_message_id"]
                    starrers = await self.bot.db.fetchrow("SELECT * FROM starrers WHERE message_id=$1", )
                    if starrers:
                        old_starrers = starrers["starrers"]
            else:
                old_starrers = starrers["starrers"]
            c = self.bot.get_channel(channel_id)
            m = await c.fetch_message(message_id)
            new_starrers = []
            try:
                for i, user_id in enumerate(old_starrers):
                    if user_id == user_id:
                        old_starrers.pop(i)
                        new_starrers = old_starrers
                        break
            except:
                pass
            await self.update_starrers(new_starrers, message_id, starboard_message)
            message_data = await self.bot.db.fetchrow("SELECT * FROM starboard WHERE original_message_id=$1 OR starboard_message_id=$1", message_id)
            if not message_data:
                return await ctx.send("A message with that ID does not exist in the starboard channel or in this channel")
            if user_id == message_data["author_id"]:
                return await ctx.send("You can't star your own message.")
            if len(new_starrers) < needed:
                await self.bot.db.execute("DELETE FROM givers WHERE user_id=$1 AND guild_id=$2 and message_id=$3", user_id, guild_id, message_id)
                await self.bot.db.execute("DELETE FROM starboard WHERE original_message_id=$1", message_data["original_message_id"])
                c = self.bot.get_channel(message_data["channel_id"])
                m = await c.fetch_message(message_data["starboard_message_id"])
                await m.delete()
                return await ctx.send("Message unstarred.")
            c = self.bot.get_channel(message_data["channel_id"])
            message = await c.fetch_message(message_data["starboard_message_id"])
            em = message.embeds[0]
            count = len(new_starrers)
            star = self.get_star(count)
            content = star+str(count)+ " | " + message.content.split(" | ")[1]
            await message.edit(content=content, embed=em)
            await self.bot.db.execute("UPDATE starboard SET stars=$1 WHERE starboard_message_id=$2", count, message_data["starboard_message_id"])
            await self.bot.db.execute("DELETE FROM givers WHERE user_id=$1 AND guild_id=$2 AND message_id=$3", user_id, guild_id, message_id)
            return await ctx.send("Message unstarred.")
        except AttributeError:
            pass

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not payload.emoji.name == "\U00002b50":
            return
        await self.star_message(channel_id=payload.channel_id, message_id=payload.message_id, user_id=payload.user_id, guild_id=payload.guild_id)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if not payload.emoji.name == "\U00002b50":
            return
        await self.unstar_message(channel_id=payload.channel_id, message_id=payload.message_id, user_id=payload.user_id, guild_id=payload.guild_id)

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def star(self, ctx, message_id:int):
        '''Manually stars a message'''
        await self.star_message(channel_id=ctx.channel.id, message_id=message_id, user_id=ctx.author.id, guild_id=ctx.guild.id, ctx=ctx)

    @commands.command()
    async def unstar(self, ctx, message_id:int):
        await self.unstar_message(channel_id=ctx.channel.id, message_id=message_id, user_id=ctx.author.id, guild_id=ctx.guild.id, ctx=ctx)
   
    @star.command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def remove(self, ctx, message_id:int):
        '''Removes a message from the starboard'''
        starboard_channel = await self.get_starboard_channel(ctx.guild.id)
        if not starboard_channel:
            return await ctx.send("This guild doesnt have a starboard channel set up. You should set one up now.")
        channel = self.bot.get_channel(starboard_channel)
        if not channel:
            await self.delete_starboard(ctx)
            return await ctx.send("The starboard channel for this guild was not found.")
        try:
            message = await channel.fetch_message(message_id)
        except:
            return await ctx.send("That message id does not correlate to a message in the starboard channel.")
        await message.delete()
        data = await self.bot.db.fetchrow("SELECT * FROM starboard WHERE starboard_message_id=$1", message_id)
        message_id = data["original_message_id"]
        starrers = await self.bot.db.fetch("SELECT * FROM starrers WHERE message_id=$1", message_id)
        for starrer in starrers:
            for user_id in starrer["starrers"]:
                await self.bot.db.execute("DELETE FROM givers WHERE user_id=$1 AND guild_id=$2 and message_id=$3", user_id, ctx.guild.id, message_id)
        await self.bot.db.execute("DELETE FROM starboard WHERE original_message_id=$1", message_id)
        await self.bot.db.execute("DELETE FROM starrers WHERE message_id=$1", message_id)
        await ctx.send("Deleted message from starboard.")
   
    @star.command()
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    async def start(self, ctx, channel:discord.TextChannel, needed:int=3):
        '''Starts the starboard in the channel provided with the given amount of stars needed'''
        starboard_channel = await self.get_starboard_channel(ctx.guild.id)
        if starboard_channel:
            return await ctx.send("You already have a starboard channel set up, use the star delete command to start over.")
        await self.bot.db.execute("INSERT INTO star_channels VALUES ($1, $2, $3)", ctx.guild.id, channel.id, needed)
        await ctx.send("Starboard has been started in "+channel.mention+" with "+str(needed)+" stars needed to star a message.")

    @star.command()
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    async def delete(self, ctx):
        '''Stops running a starboard in this guild.'''
        await self.delete_starboard(ctx)
        await ctx.send("Starboard has been stopped.")

    @star.command()
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    async def needed(self, ctx, needed:int=3):
        '''Changes how many stars are needed to star a message.'''
        if needed <= 0:
            return await ctx.send("You need to have at least one star necessary.")
        starboard_channel = await self.get_starboard_channel(ctx.guild.id)
        if not starboard_channel:
            return await ctx.send("You don't have a starboard channel in this guild, use the start command to make one.")
        await self.bot.db.execute("UPDATE star_channels SET needed=$1 WHERE guild_id=$2", needed, ctx.guild.id)
        await ctx.send("Starboard has been edited.")

    @star.command()
    @commands.guild_only()
    async def show(self, ctx, message_id:int):
        '''Shows the starred message for the id'''
        starboard_channel = await self.get_starboard_channel(ctx.guild.id)
        if not starboard_channel:
            return await ctx.send("This guild doesn't have a starboard set up.")
        else:
            c = self.bot.get_channel(starboard_channel)
            if not c:
                await self.delete_starboard(ctx)
                return await ctx.send("The starboard channel for this guild was not found.")
            try:
                m = await c.fetch_message(message_id)
            except:
                await self.bot.db.execute("DELETE FROM starboard WHERE starboard_message_id=$1", message_id)
                return await ctx.send("That message was not found.")
        await ctx.send(m.content, embed=m.embeds[0])

    @star.command()
    @commands.guild_only()
    async def random(self, ctx):
        '''Shows a random starboard message'''
        starboard_channel = await self.get_starboard_channel(ctx.guild.id)
        if not starboard_channel:
            return await ctx.send("This guild doesn't have a starboard set up.")
        message_data = await self.bot.db.fetchrow("SELECT * FROM starboard WHERE channel_id=$1 OFFSET FLOOR(RANDOM() * (SELECT COUNT(*) FROM starboard WHERE channel_id=$1)) LIMIT 1", starboard_channel)
        if not message_data:
            return await ctx.send("There are no starred messages in this guild.")
        else:
            c = self.bot.get_channel(starboard_channel)
            if not c:
                await self.delete_starboard(ctx)
                return await ctx.send("The starboard channel for this guild was not found.")
            try:
                m = await c.fetch_message(message_data["starboard_message_id"])
            except:
                await self.bot.db.execute("DELETE FROM starboard WHERE starboard_message_id=$1", message_data["starboard_message_id"])
                return await ctx.send("This command errored, try again.")
        await ctx.send(m.content, embed=m.embeds[0])

    @star.command()
    @commands.guild_only()
    async def stats(self, ctx):
        '''Shows star stats for this guild'''
        starboard_channel = await self.get_starboard_channel(ctx.guild.id)
        if not starboard_channel:
            return await ctx.send("This guild doesn't have a starboard set up.")
        star_data = await self.bot.db.fetchrow("SELECT COUNT(starboard_message_id) AS messages, SUM(stars) AS stars FROM starboard WHERE channel_id=$1", starboard_channel)
        top_3_messages = await self.bot.db.fetch("SELECT * FROM starboard WHERE channel_id=$1 ORDER BY stars DESC LIMIT 3", starboard_channel)
        top_3_authors = await self.bot.db.fetch("SELECT author_id, SUM(stars) as stars FROM starboard WHERE channel_id=$1 GROUP BY author_id ORDER BY sum(stars) DESC LIMIT 3", starboard_channel)
        top_3_givers = await self.bot.db.fetch("SELECT user_id, count(user_id) as stars FROM givers WHERE guild_id=$1 GROUP BY user_id ORDER BY count(user_id) DESC LIMIT 3", ctx.guild.id)
        desc = str(star_data["messages"]) + " starred messages with a total of " + str(star_data["stars"]) + " stars."
        color = discord.Color.gold()
        top_messages = ""
        c = self.bot.get_channel(starboard_channel)
        if not c:
            await self.delete_starboard(ctx)
            return await ctx.send("The starboard channel for this guild was not found.")
        for msg in top_3_messages:
            try:
                m = await c.fetch_message(msg["starboard_message_id"])
            except:
                await self.bot.db.execute("DELETE FROM starboard WHERE starboard_message_id=$1", msg["starboard_message_id"])
                line = " - MESSAGE NOT FOUND\n"
            else:
                line = " - ["+str(m.id)+"]("+m.jump_url+") : :star:"+str(msg["stars"])+"\n"
            top_messages+=line
        top_authors = ""
        for author in top_3_authors:
            user = self.bot.get_user(author["author_id"])
            if not user:
                await self.bot.db.execute("DELETE FROM starboard WHERE author_id=$1", author["author_id"])
                line = " - USER NOT FOUND\n"
            else:
                line = " - " + user.mention + " : :star:"+str(author["stars"])+"\n"
            top_authors+=line
        top_givers = ""
        for giver in top_3_givers:
            user = self.bot.get_user(giver["user_id"])
            if not user:
                line = " - USER NOT FOUND\n"
            else:
                line = " - " + user.mention + " : :star:"+str(giver["stars"])+"\n"
            top_givers+=line
        em = discord.Embed(title="Star Stats", description=desc, color=color)
        em.add_field(name="Top 3 Starred Messages", value=top_messages, inline=False)
        em.add_field(name="Top 3 Starred Users", value=top_authors, inline=False)
        em.add_field(name="Top 3 Star Givers", value=top_givers, inline=False)
        try:
            await ctx.send(embed=em)
        except:
            await ctx.send("There are no starred messages in this guild.")

    @star.command()
    @commands.guild_only()
    async def who(self, ctx, message_id:int):
        '''Shows who starred a message'''
        starboard_channel = await self.get_starboard_channel(ctx.guild.id)
        if not starboard_channel:
            return await ctx.send("This guild doesn't have a starboard set up.")
        message_data = await self.bot.db.fetchrow("SELECT * FROM starboard WHERE original_message_id=$1 or starboard_message_id=$1", message_id)
        if not message_data:
            return await ctx.send("That message was not found in the starboard.")
        starrers = await self.bot.db.fetchrow("SELECT * FROM starrers WHERE message_id=$1", message_data["original_message_id"])
        users = ""
        for starrer in starrers["starrers"]:
            user = self.bot.get_user(starrer)
            if not user:
                users+=" - "+str(starrer)+"\n"
                continue
            users+=" - "+user.display_name+"\n"
        gold = discord.Color.gold()
        em = discord.Embed(title="Starrers", description=users, color=gold)
        await ctx.send(embed=em)

def setup(bot):
    bot.add_cog(Star(bot))