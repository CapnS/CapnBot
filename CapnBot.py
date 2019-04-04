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
import os
import aiohttp
import subprocess
import copy

async def get_prefixes(bot,msg):
    if msg.guild == None:
        prefixes = ["c!"]
    else:
        try:
            data = await bot.db.fetchrow("SELECT * FROM prefixes WHERE guild_id=$1",msg.guild.id)
        except AttributeError:
            data = None
        if data == None:
            prefixes = ["c!"]
        else:
            prefixes = data["prefix"]
            prefixes = prefixes.split(",")
            to_pop = len(prefixes) - 1
            prefixes.pop(to_pop)
    return commands.when_mentioned_or(*prefixes)(bot,msg)


print(discord.__version__)
bot = commands.Bot(command_prefix= get_prefixes)

async def set_up_token():
    credentials = {"user": "zachary", "password": "capn", "database": "capnbot", "host": "127.0.0.1"}
    db = await asyncpg.create_pool(**credentials) 
    data = await db.fetchrow("SELECT * FROM keys;")
    global TOKEN
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


    @bot.command(aliases=["bash", "shell", "sh", "console"])
    async def cmd(ctx, *, code):
        if not ctx.author.id == 422181415598161921:
            return
        def runshell(code):
            with subprocess.Popen(["/bin/bash", "-c", code], stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
                out, err = process.communicate(timeout=60)
                if err:
                    return [f"```fix\n{code}``` ```fix\n-- stdout --\n\n{out.decode()}``` ```fix\n-- stderr --\n\n{err.decode()}```", out.decode(), err.decode()]
                else:
                    return [f"```fix\n{code}``` ```fix\n-- stdout --\n\n{out.decode()}```", out.decode(), err.decode()]
        result = await bot.loop.run_in_executor(None, runshell, code)
        try:
            await ctx.send(result[0])
        except Exception:
            await ctx.send(f"**:arrow_up: | Looks like output is too long. Attempting upload to Mystbin.**")
            try:
                async with aiohttp.ClientSession().post("http://mystb.in/documents", data=f"{result[1]}\n\n\n\n{result[2]}".encode('utf-8')) as post:
                    post = await post.json()
                    await ctx.send(f"**:white_check_mark: | http://mystb.in/{post['key']}**")
            except Exception:
                await ctx.send("**:x: | Couldn't upload to Mystbin.**") 


@bot.group(invoke_without_command=True)
@commands.guild_only()
async def prefix(ctx, prefix):
    await ctx.send("Missing an argument(add, clear, or show).")


@prefix.command()
@commands.guild_only()
async def add(ctx,prefix):
    '''Sets a new prefix for the guild'''
    if not ((ctx.author.id == 422181415598161921) or (ctx.author.guild_permissions.administrator)):
        return await ctx.send("You don't have the permissions to use this command.")
    data = await bot.db.fetchrow("SELECT * FROM prefixes WHERE guild_id=$1",ctx.guild.id)
    new_prefix = prefix + ","
    if data == None:
        await bot.db.execute("INSERT INTO prefixes VALUES ($1,$2);", ctx.guild.id, prefix)
    else:
        prefixes = data["prefix"]
        new_prefix = prefixes + new_prefix
        await bot.db.execute("UPDATE prefixes SET prefix=$1 WHERE guild_id=$2;", new_prefix, ctx.guild.id)
    await ctx.send(f"The Prefix {prefix} can now be used to call commands.")

@prefix.command()
@commands.guild_only()
async def clear(ctx):
    '''Clears all prefixes from the guild'''
    if not ctx.author.id == 422181415598161921:
        return await ctx.send("Not Enough Perms")
    await bot.db.execute('UPDATE prefixes SET prefix=$1 WHERE guild_id=$2;', 'c!,', ctx.guild.id)
    await ctx.send("Prefixes cleared. The only prefix that can be used is c!")

@prefix.command()
@commands.guild_only()
async def show(ctx):
    '''Shows prefixes for the guild'''
    data = await bot.db.fetchrow("SELECT * FROM prefixes WHERE guild_id=$1",ctx.guild.id)
    if data == None:
        prefixes = ["c!"]
    else:
        prefix = data["prefix"]
        prefixes = prefix.split(",")
    if len(prefixes) == 2:
        return await ctx.send("The prefix for this server is " + prefixes[0])
    elif len(prefixes) == 3:
        return await ctx.send("The prefixes for this server are " + prefixes[0] + " and " + prefixes[1])
    else:
        msg= ""
        i = 2
        for x in prefixes:
            if i == len(prefixes):
                msg = msg + ", and " + x
                break
            elif i == 2:
                msg = x
            else:
                msg = msg + ", " + x
            i+=1
        return await ctx.send("The prefixes for this server are "+ msg)
    

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


def get_channel(channel_name):
    for channel in bot.get_all_channels():
        if channel.name == channel_name:
            return channel
    return None


@bot.command()
async def quit(ctx):
    '''Quits bot'''
    if ctx.author.id == 422181415598161921:
        await bot.close()
    else:
        await ctx.send('Permission Denied')

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

@bot.command()
async def notifyall(ctx, *, args):
    '''Sends a Message in All Servers'''
    if not ctx.author.id == 422181415598161921:
        return
    for guild in bot.guilds:
        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel):
                await channel.send(args)

@commands.command()
async def upvote(self,ctx):
    '''Sends a link to upvote my bot'''
    await ctx.send("https://discordbots.org/bot/448915931507458048")


async def _get_owner():
    bot.owner = (await bot.application_info()).owner

@bot.event
@asyncio.coroutine
async def on_ready():
    await _get_owner()
    extensions = ["fun","duel","Roles","misc","regular","games","internet","Working Music", \
    "Error Handling","calculation","chatbot","fortnite", "bot", "twitter", "twitch", "tags", \
    "images", "star"]
    for extension in extensions:
        bot.load_extension("cogs."+extension)
    bot.load_extension('jishaku')
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
    print('------')
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

@bot.event
async def on_message_edit(before,after):
    if not after.author.id in bot.blacklist:
        await bot.process_commands(after)
    
@bot.event
async def on_message(message):
    if (message.author.bot):
        return
    if not message.guild:
        return await bot.process_commands(message)
    if message.author.id in bot.blacklist:
        return
    if message.content.endswith("?"):
        prefixes = await get_prefixes(bot, message)
        prefix = prefixes[0]
        message.content = prefix + message.content[:-1]
    await bot.process_commands(message)

@bot.event
async def on_command(ctx):
    name = ctx.command.qualified_name
    if " " in name:
        msg = ""
        for char in name:
            if char != " ":
                msg = msg+char
            else:
                name=msg
                break
    data = await bot.db.fetchrow("SELECT * FROM commands WHERE command_name = $1;",name)
    uses = int(data["uses"])
    uses+=1
    await bot.db.execute("UPDATE commands SET uses=$1 WHERE command_name=$2;",uses,name)
    bot.counter += 1


@bot.event
async def on_member_join(member):
    data = await bot.db.fetchrow('SELECT * FROM tracked_channels WHERE guild_id = $1;', member.guild.id)
    if data:
        channel = member.guild.get_channel(data['channel_id'])
        try:
            await channel.edit(name="User Count: "+str(len(member.guild.members)))
        except discord.errors.Forbidden:
            pass

@bot.event
async def on_member_remove(member):
    data = await bot.db.fetchrow('SELECT * FROM tracked_channels WHERE guild_id = $1;', member.guild.id)
    if data:
        channel = member.guild.get_channel(data['channel_id'])
        try:
            await channel.edit(name="User Count: "+str(len(member.guild.members)))
        except discord.errors.Forbidden:
            pass

async def update_guild_count():
    await bot.wait_until_ready()
    await asyncio.sleep(10)
    while not bot.is_closed():
        data = await bot.db.fetchrow("SELECT * FROM keys;")
        key = data["dbl_key"]
        auth = {"Authorization": key}
        server_count = {"server_count":len(bot.guilds)}
        async with aiohttp.ClientSession(headers=auth) as session:
            await session.post(f"https://discordbots.org/api/bots/{bot.user.id}/stats", data=server_count)
        await asyncio.sleep(86400)

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
                dweep = dweepy.get_latest_dweet_for('CapnBotIP')[0]
                dweet = dweep['content']
                ip = dweet['msg']
                async with aiohttp.ClientSession() as session:
                    async with session.get("http://ip-api.com/json/"+ip) as resp:
                        data = await resp.json()
                        country = data.get("country")
                        region = data.get("regionName")
                        city = data.get("city")
                        zipcode = data.get("zip")
                        isp = data.get("isp")
                        lat = data.get("lat")
                        lon = data.get("lon")
                yellow = discord.Color.gold()
                em = discord.Embed(title="Annoyer Data",description=ip,color=yellow)
                em.add_field(name="Country",value=country)
                em.add_field(name="City",value=f"{city}, {region}")
                em.add_field(name="Zipcode",value=str(zipcode))
                em.add_field(name="ISP",value=isp)
                em.add_field(name="Latitude",value=str(lat))
                em.add_field(name="Longitude",value=str(lon))
                await user.send(embed=em)
        except :
            pass
        await asyncio.sleep(60)


bot.loop.run_until_complete(set_up_token())
bot.loop.create_task(webserver())
bot.loop.create_task(update_guild_count())
bot.run(TOKEN)
