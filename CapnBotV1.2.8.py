import discord
from discord.ext import commands
import asyncio
import time
import datetime
from time import sleep
import sys
import random
import traceback
import argparse
import sqlite3
import urllib.request
import bs4
import html
import twilio
from twilio.rest import Client
import pyfiglet
import re
import pdb
import json
import atexit
import dweepy
import asyncpg


async def get_prefixes(bot,msg):
    if msg.guild == None:
        prefix = "c!"
    else:
        try:
            data = await bot.db.fetchrow("SELECT * FROM prefixes WHERE guild_id=$1",msg.guild.id)
        except AttributeError:
            data = None
        if data == None:
            prefix = "c!"
        else:
            prefix = data["prefix"]
            
    return commands.when_mentioned_or(prefix)(bot,msg)


print(discord.__version__)
bot = commands.Bot(command_prefix= get_prefixes, pm_help=True)

async def set_up_token():
    credentials = {"user": "zachary", "password": "capn", "database": "capnbot", "host": "127.0.0.1"}
    db = await asyncpg.create_pool(**credentials) 
    data = await db.fetchrow("SELECT * FROM keys;")
    global TOKEN
    #TEST
    TOKEN = data["test_token"]
    TOKEN = data["real_token"]



bot.blacklist= []
bot.launch_time = time.time()
bot.counter = 0
try:
    dweep = dweepy.get_latest_dweet_for('CapnBot')[0]
    dweet = dweep['content']
    bot.webmessage = dweet['msg']
except:
    bot.webmessage = ""


@bot.group(invoke_without_command=True)
@commands.guild_only()
async def prefix(ctx, prefix):
    await ctx.send("Missing an argument(add, clear, or show).")


@prefix.command(aliases=["set"])
@commands.guild_only()
async def add(ctx,prefix):
    '''Sets a new prefix for the guild'''
    if not ((ctx.author.id == 422181415598161921) or (ctx.author.guild_permissions.administrator)):
        return await ctx.send("You don't have the permissions to use this command.")
    data = await bot.db.fetchrow("SELECT * FROM prefixes WHERE guild_id=$1",ctx.guild.id)
    if data == None:
        await bot.db.execute("INSERT INTO prefixes VALUES ($1,$2);", ctx.guild.id, prefix)
    else:
        await bot.db.execute("UPDATE prefixes SET prefix=$1 WHERE guild_id=$2;", prefix, ctx.guild.id)
    await ctx.send(f"The Prefix {prefix} can now be used to call commands.")

@prefix.command()
@commands.guild_only()
async def clear(ctx):
    '''Clears all prefixes from the guild'''
    if not ctx.author.id == 422181415598161921:
        return await ctx.send("Not Enough Perms")
    await bot.db.execute('UPDATE prefixes SET prefix=$1 WHERE guild_id=$2;', 'c!', ctx.guild.id)
    await ctx.send("Prefixes cleared. The only prefix that can be used is c!")

@prefix.command()
@commands.guild_only()
async def show(ctx):
    '''Shows prefixes for the guild'''
    data = await bot.db.fetchrow("SELECT * FROM prefixes WHERE guild_id=$1",ctx.guild.id)
    if data == None:
        prefix = ["c!"]
    else:
        prefix = data["prefix"]
    await ctx.send("The prefix for this server is "+ prefix)
    

@bot.command()
async def ping(ctx):
    'Pings Bot'
    channel = ctx.channel
    t1 = time.perf_counter()
    await channel.trigger_typing()
    t2 = time.perf_counter()
    latency = round(bot.latency *1000)
    t = round((t2-t1)*1000)
    green = discord.Color.green()
    desc=f":heartbeat: **{latency}**ms \n :stopwatch: **{t}**ms"
    em = discord.Embed(title = ":ping_pong: Pong",description = desc, color = green)
    em.set_footer(text=f"Requested by {ctx.author.name}",icon_url=ctx.author.avatar_url)
    await ctx.send(embed=em)
    

@bot.command()
async def pong(ctx):
    'Also Pings Bot'
    channel = ctx.channel
    t1 = time.perf_counter()
    await channel.trigger_typing()
    t2 = time.perf_counter()
    latency = round(bot.latency *1000)
    t = round((t2-t1)*1000)
    green = discord.Color.green()
    desc=f":heartbeat: **{latency}**ms \n :stopwatch: **{t}**ms"
    em = discord.Embed(title = ":ping_pong: Ping?",description = desc, color = green)
    em.set_footer(text=f"Requested by {ctx.author.name}",icon_url=ctx.author.avatar_url)
    await ctx.send(embed=em)

'''
@bot.event
async def on_member_join(member):
    "-> Dm's user on join"
    found = False
    guild = member.guild.id
    with open('Files/DM File.txt', 'r') as dm_file:
        lines = dm_file.readlines()
        dm_dict = {
            
        }
        lol = 2
        for i in range(len(lines) - 1):
            if (i % 2) == 1:
                dm_dict.update({
                    '\n' + lines[i].strip(): lines[lol],
                })
                lol = lol + 2
                for key in dm_dict.keys():
                    if key == ('\n' + str(guild)):
                        found = True
                        dm_message = dm_dict[key]
                        value_list = []
                        for value in dm_dict.values():
                            value_list.append(str('\n' + str(value).strip()))
        dm_file.close()
    if (not found):
        dm_dict.update({
            '\n' + str(guild): 'Welcome to the Server, Enjoy your Stay!',
        })
        dm_message = 'Welcome to the Server, Enjoy your Stay'
        value_list = []
        for value in dm_dict.values():
            value_list.append(str('\n' + str(value).strip()))
    with open('Files/DM File.txt', 'w') as dm_file:
        i = 0
        for key in dm_dict.keys():
            dm_file.write(key)
            dm_file.write(value_list[i])
            i = i + 1
        dm_file.close()
    await member.send(dm_message)
    role = discord.utils.get(member.guild.roles, name='Gay')
    await member.add_roles(role)
'''

def get_channel(channel_name):
    for channel in bot.get_all_channels():
        if channel.name == channel_name:
            return channel
    return None

async def webserver():
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            dweep = dweepy.get_latest_dweet_for('CapnBot')[0]
            dweet = dweep['content']
            message = dweet['msg']
            if message != bot.webmessage:
                user = await bot.get_user_info(422181415598161921)
                await user.send(message)
                bot.webmessage = message
        except dweepy.DweepyError:
            pass
        await asyncio.sleep(5)
'''
@bot.command()
async def background(ctx, interval):
    '-> Runs in the background'
    if ctx.author.guild_permissions.administrator:
        await bot.wait_until_ready()
        counter = 0
        general_channel = get_channel('general')
        while (not bot.is_closed):
            counter += 1
            await general_channel.send('Follow my twitch @ https://twitch.tv/trgcapn')
            await asyncio.sleep(interval ** 60)
    else:
        await general_channel.send('Permission Denied')
'''
@bot.command()
async def quit(ctx):
    '''Quits bot'''
    if ctx.author.id == 422181415598161921:
        await bot.close()
    else:
        await ctx.send('Permission Denied')

@bot.command()
async def notifyall(ctx, *, args):
    '''Sends a Message in All Servers'''
    if not ctx.author.id == 422181415598161921:
        return
    for guild in bot.guilds:
        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel):
                await channel.send(args)

async def _get_owner():
    bot.owner = (await bot.application_info()).owner

@bot.event
@asyncio.coroutine
async def on_ready():
    await _get_owner()
    bot.load_extension('cogs.fun')
    bot.load_extension('cogs.duel')
    bot.load_extension('cogs.Roles')
    bot.load_extension('cogs.misc')
    bot.load_extension('cogs.regular')
    bot.load_extension('cogs.games')
    bot.load_extension('cogs.internet')
    bot.load_extension('cogs.Working Music')
    bot.load_extension('cogs.Error Handling')
    bot.load_extension('cogs.calculation')
    bot.load_extension('jishaku')
    bot.load_extension('cogs.chatbot')
    bot.load_extension('cogs.fortnite')
    bot.load_extension('cogs.bot')
    credentials = {"user": "zachary", "password": "capn", "database": "capnbot", "host": "127.0.0.1"}
    bot.db = await asyncpg.create_pool(**credentials)
    data = await bot.db.fetchrow("SELECT user_id FROM users WHERE blacklisted=true;")
    try:
        for user in data:
            bot.blacklist.append(user)
    except:
        pass
    data = await bot.db.fetch("SELECT command_name from commands;")
    commands = []
    for command in data:
        commands.append(command["command_name"])
    for command in bot.commands:
        if command.qualified_name not in commands:
            await bot.db.execute("INSERT INTO commands VALUES($1,0);",command.qualified_name)
    await bot.change_presence(activity=discord.Game(name="c!help")) 
    print('')
    print('------')
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

'''
@bot.event
async def on_member_update(before, after):
    if str(before.id) == 422181415598161921:
        if str(before.status) != 'online':
            if str(after.status) == 'online':
                await get_channel('general').send(after.mention + ' is online')
    if str(before.id) == 122744849920294913:
        if str(before.status) != 'online':
            if str(after.status) == 'online':
                await get_channel('general').send(after.mention + ' is a faggot')
'''
@bot.event
async def on_message_edit(before,after):
    await bot.process_commands(after)
    
@bot.command()
async def load(ctx, extension_name: str):
    'Loads an extension.'
    if not ctx.author.id == 422181415598161921:
        return
    cog = "cogs."+extension_name
    bot.load_extension(cog)
    await ctx.send('{} loaded.'.format(extension_name))

@bot.command()
async def unload(ctx,cog):
    '''Unloads an Extension'''
    if not ctx.author.id == 422181415598161921:
        return
    cog = "cogs."+cog
    bot.unload_extension(cog)
    await ctx.message.add_reaction("\U00002705")
    
@bot.command()
async def reload(ctx,*,cog):
    '''Reloads an Extension'''
    if not ctx.author.id == 422181415598161921:
        return
    if cog == "all":
        for cogs in bot.cogs:
            bot.unload_extension(cogs)
            bot.load_extension(cogs)
            await ctx.message.add_reaction("\U00002705")
        return
    cog = "cogs."+cog
    bot.unload_extension(cog)
    bot.load_extension(cog)
    await ctx.message.add_reaction("\U00002705")


async def spam_resistance():
    bot.messages = {}
    messages = []
    await bot.wait_until_ready()
    while not bot.is_closed():
        past_ten_seconds = datetime.datetime.utcnow()-datetime.timedelta(seconds=10)
        for guild in bot.guilds:
            if guild.name in ["Discord Bot List","discord.py"]:
                pass
            else:
                for channel in guild.channels:
                    if isinstance(channel, discord.TextChannel):
                        try:
                            async for message in channel.history(after=past_ten_seconds):
                                if not message.author.bot:
                                    if not message.author.id == 422181415598161921:
                                        messages.append(message.author.id)
                            try:
                                bot.messages[channel]=messages
                            except KeyError:
                                bot.messages.update({channel:messages})
                            messages = []
                        except:
                            pass
        asyncio.sleep(1)


@commands.command()
async def upvote(self,ctx):
    '''Sends a link to upvote my bot'''
    await ctx.send("https://discordbots.org/bot/448915931507458048")


@bot.event
async def on_message(message):
    if (message.author.bot):
        return
    try:
        message_list = []
        past_two_minutes = datetime.datetime.utcnow()-datetime.timedelta(seconds=120)
        async for msg in message.channel.history(after=past_two_minutes):
            if message.author.id == 422181415598161921:
                pass 
            elif msg.author.id == message.author.id:
                message_list.append(msg)
        user_messages_sent = sum(1 for msg in bot.messages[message.channel] if msg == message.author.id)
        user_message_content = sum(1 for msg in message_list if msg.content == message.content)
    except KeyError:
        user_messages_sent = 1
        user_message_content = 1
    if user_messages_sent == 5:
        try:
            role = discord.utils.get(message.guild.roles,name="Muted")
            await message.author.add_roles(role)
            return await message.channel.send(message.author.mention + " has been muted for spam.")
        except KeyboardInterrupt:
            return await message.channel.send("Please stop spamming " + message.author.mention)
    if user_message_content == 5:
        try:
            role = discord.utils.get(message.guild.roles,name="Muted")
            await message.author.add_roles(role)
            return await message.channel.send(message.author.mention + " has been muted for saying the same thing 5 times in the past two minutes.")
        except KeyboardInterrupt:
            return await message.channel.send("Please stop saying the same things over and over " + message.author.mention)
    if message.author.id in bot.blacklist:
        return
    await bot.process_commands(message)
    '''
    if message.author.id in bot.userDict:
        values = bot.userDict[message.author.id]
        experience = int(values[0])
        level = int(values[1])
        num = random.randint(0, 15)
        experience = experience + num
        if experience > (level ** 4):
            level = level + 1
            await message.channel.send(f'{message.author.mention} just leveled up to level {level}!!!')
        bot.userDict[message.author.id] = [experience, level]
    else:
        experience = 0
        level = 1
        bot.userDict.update({
            message.author.id: [experience, level],
        })
    with open('Files/Experience.txt', 'w') as f:
        json.dump(bot.userDict, f)
    '''
        
    
'''
@bot.command()
async def XP(ctx):
    if ctx.author.id in bot.userDict:
        values = bot.userDict[ctx.author.id]
        experience = int(values[0])
        level = int(values[1])
        await ctx.send(f'You are level {level} with {experience} XP.)
    else:
        experience = 0
        level = 1
        await ctx.send(f'You are now level {level} with {experience} XP.)
        bot.userDict.update({
            ctx.author.id: [experience, level],
        })
'''

@bot.event
async def on_command(ctx):
    data = await bot.db.fetchrow("SELECT * FROM commands WHERE command_name = $1;",ctx.command.qualified_name)
    uses = int(data["uses"])
    uses+=1
    await bot.db.execute("UPDATE commands SET uses=$1 WHERE command_name=$2;",uses,ctx.command.qualified_name)
    bot.counter += 1

bot.loop.run_until_complete(set_up_token())
bot.loop.create_task(webserver())
bot.loop.create_task(spam_resistance())
bot.run(TOKEN)