# -*- coding: utf-8 -*-

from discord.ext import commands
import discord

class Star(commands.Cog):
    """Starboard commands"""

    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not payload.emoji.name == "\U00002b50":
            return
        channel_data = await self.bot.db.fetchrow("SELECT * FROM star_channels WHERE guild_id=$1", payload.guild_id)
        if not channel_data:
            return
        starrers = await self.bot.db.fetchrow("SELECT * FROM starrers WHERE message_id=$1", payload.message_id)
        if starrers:
            old_starrers = starrers["starrers"]
            if payload.user_id in old_starrers:
                return
        c = self.bot.get_channel(payload.channel_id)
        if not c:
            return
        m = await c.fetch_message(payload.message_id)
        if not m:
            return
        count = 1
        for r in m.reactions:
            if r.name ==  "\U00002b50":
                count = r.count
                break
        if count < channel_data["needed"]:
            if starrers:
                new_starrers = old_starrers.append(payload.user_id)
                await self.bot.db.execute("UPDATE starrers SET starrers=$1 WHERE message_id=$2", new_starrers, payload.message_id)
            else:
                new_starrers = [payload.user_id]
                await self.bot.db.execute("INSERT INTO starrers VALUES ($1, $2)", payload.message_id, new_starrers)
            return      
        message_data = await self.bot.db.fetchrow("SELECT * FROM starboard WHERE original_message_id=$1", payload.message_id)
        if not message_data:
            message_data = await self.bot.db.fetchrow("SELECT * FROM starboard WHERE starboard_message_id=$1", payload.message_id)
            if not message_data:
                c = self.bot.get_channel(payload.channel_id)
                if not c:
                    return
                m = await c.fetch_message(payload.message_id)
                if payload.user_id == m.author.id:
                    return
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
                channel = self.bot.get_channel(channel_data["channel_id"])
                count = 1
                for r in m.reactions:
                    if r.name ==  "\U00002b50":
                        count = r.count
                        break
                content = ":star:"+str(count)+ " | "+channel.mention
                try:
                    message = await channel.send(content, embed=em)
                except:
                    return
                await self.bot.db.execute("INSERT INTO starboard VALUES($1, $2, $3, $4)", payload.message_id, message.id, message.channel.id, count)
                return
            else:
                starrers = await self.bot.db.fetchrow("SELECT * FROM starrers WHERE message_id=$1", message_data["original_message_id"])
                if starrers:
                    old_starrers = starrers["starrers"]
                    if payload.user_id in old_starrers:
                        return
                    else:
                        new_starrers = old_starrers.append(payload.user_id)
        c = self.bot.get_channel(message_data["channel_id"])
        if not c:
            return
        message = await c.fetch_message(message_data["starboard_message_id"])
        if not message:
            return
        em = message.embeds[0]
        count = message_data["stars"] + 1
        content = ":star:"+str(count)+ " | " + c.mention
        try:
            await message.edit(content=content, embed=em)
        except:
            return
        await self.bot.db.execute("UPDATE starboard SET count=$1 WHERE starboard_message_id=$2", count, message_data["starboard_message_id"])
        await self.bot.db.execute("UPDATE starrers SET starrers=$1 WHERE message_id=$2", new_starrers, payload.message_id)

    @commands.group(invoke_without_command=True)
    async def star(self, ctx, message_id):
        '''Manually stars a message'''
        channel_data = await self.bot.db.fetchrow("SELECT * FROM star_channels WHERE guild_id=$1", ctx.guild.id)
        if not channel_data:
            return await ctx.send("You don't have a starboard setup, ask an admin to set one up for this guild.")
        starrers = await self.bot.db.fetchrow("SELECT * FROM starrers WHERE message_id=$1", message_id)
        if starrers:
            old_starrers = starrers["starrers"]
            if ctx.author.id in old_starrers:
                return
        m = await ctx.channel.fetch_message(message_id)
        if not m:
            c = self.bot.get_channel(channel_data["channel_id"])
            m = await c.fetch_message(message_id)
            if not m:
                return await ctx.send("That message was not sent in this channel or in the starboard channel.")
        count = 1
        for r in m.reactions:
            if r.name ==  "\U00002b50":
                count = r.count
                break
        if count < channel_data["needed"]:
            if starrers:
                new_starrers = old_starrers.append(ctx.author.id)
                await self.bot.db.execute("UPDATE starrers SET starrers=$1 WHERE message_id=$2", new_starrers, message_id)
            else:
                new_starrers = [ctx.author.id]
                await self.bot.db.execute("INSERT INTO starrers VALUES ($1, $2)", message_id, new_starrers)
            return      
        message_data = await self.bot.db.fetchrow("SELECT * FROM starboard WHERE original_message_id=$1", message_id)
        if not message_data:
            message_data = await self.bot.db.fetchrow("SELECT * FROM starboard WHERE starboard_message_id=$1", message_id)
            if not message_data:
                c = self.bot.get_channel(ctx.channelid)
                if not c:
                    return
                m = await c.fetch_message(message_id)
                if ctx.author.id == m.author.id:
                    return
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
                channel = self.bot.get_channel(channel_data["channel_id"])
                count = 1
                for r in m.reactions:
                    if r.name ==  "\U00002b50":
                        count = r.count
                        break
                content = ":star:"+str(count)+ " | "+channel.mention
                try:
                    message = await channel.send(content, embed=em)
                except:
                    return
                await self.bot.db.execute("INSERT INTO starboard VALUES($1, $2, $3, $4)", message_id, message.id, message.channel.id, count)
                return
            else:
                starrers = await self.bot.db.fetchrow("SELECT * FROM starrers WHERE message_id=$1", message_data["original_message_id"])
                if starrers:
                    old_starrers = starrers["starrers"]
                    if ctx.author.id in old_starrers:
                        return
                    else:
                        new_starrers = old_starrers.append(ctx.author.id)
        c = self.bot.get_channel(message_data["channel_id"])
        if not c:
            return
        message = await c.fetch_message(message_data["starboard_message_id"])
        if not message:
            return
        em = message.embeds[0]
        count = message_data["stars"] + 1
        content = ":star:"+str(count)+ " | " + c.mention
        try:
            await message.edit(content=content, embed=em)
        except:
            return
        await self.bot.db.execute("UPDATE starboard SET count=$1 WHERE starboard_message_id=$2", count, message_data["starboard_message_id"])
        await self.bot.db.execute("UPDATE starrers SET starrers=$1 WHERE message_id=$2", new_starrers, message_id)
        await ctx.send("Message Starred.")
    
    @star.command()
    async def remove(self, ctx, message_id):
        '''Removes a message from the starboard'''
        if not ctx.author.guild_permissions.administrator:
            return
        channel_data = await self.bot.db.fetchrow("SELECT * FROM star_channels WHERE guild_id=$1", ctx.guild.id)
        if not channel_data:
            return await ctx.send("This guild doesnt have a starboard channel set up. You should set one up now.")
        channel = self.bot.get_channel(channel_data["channel_id"])
        message = await channel.fetch_message(message_id)
        if not message:
            return await ctx.send("That message id does not correlate to a message in the starboard channel.")
        try:
            await message.delete()
            data = await self.bot.db.fetchrow("SELECT * FROM starboard WHERE starboard_message_id=$1", message_id)
            message_id = data["original_message_id"]
            await self.bot.db.execute("DELETE FROM starboard WHERE original_message_id=$1", message_id)
            await self.bot.db.execute("DELETE FROM starrers WHERE message_id=$1", message_id)
            await ctx.send("Deleted message from starboard.")
        except:
            await ctx.send("Could not delete that message.")
        
    @star.command()
    async def start(self, ctx, channel:discord.Channel, needed:int=3):
        '''Starts the starboard in the channel provided with the given amount of stars needed'''
        channel_data = await self.bot.db.fetchrow("SELECT * FROM star_channels WHERE guild_id=$1", ctx.guild.id)
        if channel_data:
            return await ctx.send("You already have a starboard channel set up, use the star delete command to start over.")
        await self.bot.db.execute("INSERT INTO star_channels VALUES ($1, $2, $3)", ctx.guild.id, channel.id, needed)
        await ctx.send("Starboard has been started in "+channel.mention+" with "+str(needed)+" stars needed to star a message.")

    @star.command()
    async def delete(self, ctx):
        '''Stops running a starboard in this guild.'''
        channel_data = await self.bot.db.fetchrow("SELECT * FROM star_channels WHERE guild_id=$1", ctx.guild.id)
        if not channel_data:
            return await ctx.send("You don't have a starboard channel in this guild, use the start command to make one.")
        await self.bot.db.execute("DELETE FROM star_channels WHERE guild_id=$1", ctx.guild.id)
        await ctx.send("Starboard has been stopped.")

    @star.command()
    async def needed(self, ctx, needed:int=3):
        '''Changes how many stars are needed to star a message.'''
        channel_data = await self.bot.db.fetchrow("SELECT * FROM star_channels WHERE guild_id=$1", ctx.guild.id)
        if not channel_data:
            return await ctx.send("You don't have a starboard channel in this guild, use the start command to make one.")
        await self.bot.db.execute("UPDATE star_channels SET needed=$1 WHERE guild_id=$2", needed, ctx.guild.id)
        await ctx.send("Starboard has been edited.")

def setup(bot):
    bot.add_cog(Star(bot))
