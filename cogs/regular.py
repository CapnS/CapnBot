import discord
from discord.ext import commands
from datetime import datetime
import matplotlib
import psutil
import time
import json
import dweepy
import asyncio
import dbl
import traceback



class Regular():

    def __init__(self, bot):
        self.bot = bot
        self.process = psutil.Process()
        self.start_time = time.time()
        bot.remove_command("help")
    

    @commands.command()
    async def remove_after(self,ctx, seconds:int=3):
        '''adds and removes a reaction'''
        msg = await ctx.send(f"Removing Reaction in {seconds} seconds.")
        await msg.add_reaction("\U00002b50")
        sec = seconds
        for i in range(seconds):
            await msg.edit(content=f"Removing Reaction in {sec} seconds.")
            sec-=1
            await asyncio.sleep(1)
        await msg.remove_reaction("\U00002b50",self.bot.user)
        await msg.edit(content="Removed Reaction")



    @commands.command(aliases = ["ubl"])
    async def unblacklist(self,ctx,user: discord.Member):
        '''unblacklists a user'''
        if not ctx.author.id == 422181415598161921:
            return
        found=False
        i=0
        for member in self.bot.blacklist:
            if member == user.id:
                self.bot.blacklist.pop(i)
                await ctx.send("Un-Blacklisted"+user.name)
                await self.bot.db.execute("UPDATE users SET blacklisted=false WHERE user_id=$1",user.id)
                found=True
            i+=1
        if not found:
            await ctx.send("User not Blacklisted")


    @commands.command(aliases = ["bl"])
    async def blacklist(self,ctx, user: discord.Member,*,reason=None):
        '''blacklists a user'''
        if not ctx.author.id == 422181415598161921:
            return
        for key in self.bot.blacklist:
            if user.id == key:
                return await ctx.send("User already blacklisted.")
        if reason:
            em = discord.Embed(title = f"Blacklisted {user.name}")
            em.set_thumbnail(url=user.avatar_url)
            em.color = discord.Color.red()
            await ctx.send(embed=em)
        else:
            em = discord.Embed(title = f"Blacklisted {user.name}")
            em.color = discord.Color.red()
            em.set_thumbnail(url=user.avatar_url)
            await ctx.send(embed=em)
        self.bot.blacklist.append(user.id)
        await self.bot.db.execute("UPDATE users SET blacklisted=true WHERE user_id=$1",user.id)

    @commands.command(aliases=["bls"])
    async def blacklisted(self,ctx):
        '''shows all blacklisted users'''
        blacklisted_users = ''
        for user in self.bot.blacklist:
            user_object = await self.bot.get_user_info(user)
            blacklisted_users = blacklisted_users + "\n"+ user_object.name
        em = discord.Embed(title="Blacklisted Users:", description= blacklisted_users)
        em.color = discord.Color.red()
        await ctx.send(embed=em)            
            


              
    @commands.command()
    async def delete(self, ctx, amount:int):
        'Deletes Messages'
        if ctx.author.guild_permissions.administrator:
            try:
                await ctx.channel.purge(limit=amount+1)
                await ctx.send(amount + ' Messages Deleted')
            except discord.errors.ClientException:
                await ctx.send('Can only delete in range 2, 100.')
        else:
            return

    @commands.command()
    async def purge(self,ctx,user:discord.Member, num : int):
        if ctx.author.guild_permissions.administrator:
            def check(message):
                return message.author == user
            await ctx.channel.purge(limit = num, check=check)
            
    @commands.command()
    async def clean(self,ctx,num:int):
        if not ctx.author.id == 422181415598161921 or ctx.author.guild_permissions.administrator:
            return
        else:
            def check(message):
                return message.author == self.bot.user
            await ctx.channel.purge(limit = num+1, check=check)
            

    @commands.command(aliases=['info'])
    async def userinfo(self, ctx, *, user: discord.Member=None):
        """Shows information about a User"""

        if user is None:
            user = ctx.author

        roles = [role.mention for role in user.roles if not role.is_default()]

        voice = user.voice
        if voice is not None:
            vc = voice.channel
            other_people = len(vc.members) - 1
            voice = f'In {vc.name} with {other_people} other(s)' if other_people else f'In {vc.name} all by themselves'
        else:
            voice = 'Not connected'

        pos = sorted(ctx.guild.members, key=lambda m: m.joined_at).index(user)+1
        blue = discord.Color.blue()
        e = discord.Embed(color=blue)
        e.set_thumbnail(url=user.avatar_url)
        e.add_field(name='User:', value=f"{user}")
        e.add_field(name='User ID:', value=f"{user.id}")
        e.add_field(name='Status:', value=f"{user.status}".title())
        e.add_field(name='Join Position:', value=f"#{pos}")
        e.add_field(name='Created:', value=f"{user.created_at.strftime('%b %d, %Y')}")
        e.add_field(name='Joined server:', value=f"{user.joined_at.strftime('%b %d, %Y')}")
        e.add_field(name='Voice:', value=f"{voice}")
        e.add_field(name=f'Roles: ({len(roles)})', value=f"{chr(173)}{', '.join(roles)}" if len(roles) < 15 else f"{len(roles)} Roles")
        await ctx.send(embed=e)

    @commands.command()
    async def kick(self, ctx, user: discord.Member, reason):
        'Kicks a User'
        try:
            if ctx.author.guild_permissions.administrator:
                await user.send(text='You were kicked because' + str(reason))
                await user.kick()
                await ctx.send('Kicked {}'.format(user.name))
            else:
                await ctx.send('Permission Denied.')
        except:
            await ctx.send('User not found')

    @commands.command()
    async def ban(self, ctx, user: discord.Member,*, reason):
        'Bans a User'
        try:
            if ctx.author.guild_permissions.administrator:
                await ctx.send('Banned {}'.format(user.name))
                await user.send((('You were banned from ' + str(ctx.guild.name)) + ' because ') + reason)
                await ctx.guild.ban(user)
            else:
                await ctx.send('Permission Denied.')
        except :
            await ctx.send('Failed to Ban')

    @commands.command()
    async def unban(self, ctx, user):
        'BROKEN '
        try:
            if ctx.author.guild_permissions.administrator:
                banned_user = await self.bot.get_user_info(user)
                guild = ctx.guild
                await ctx.send('Unbanned {}'.format(user.name))
                await guild.unban(banned_user)
            else:
                await ctx.send('Permission Denied.')
        except:
            await ctx.send('User not found')

    @commands.command()
    async def mute(self, ctx, user: discord.Member):
        'Mutes a user'
        try:
            if ctx.author.guild_permissions.administrator:
                role = discord.utils.get(ctx.guild.roles, name='Muted')
                await user.add_roles(role)
                await ctx.send('Muted {}'.format(user.name))
            else:
                await ctx.send('Permission Denied.')
        except KeyboardInterrupt:
            await ctx.send('User Not Found')

    @commands.command()
    async def unmute(self, ctx, user: discord.Member):
        'Unmutes a User'
        try:
            if ctx.author.guild_permissions.administrator:
                role = discord.utils.get(ctx.guild.roles, name='Muted')
                await user.remove_roles(role)
                await ctx.send('Unmuted {}'.format(user.name))
            else:
                await ctx.send('Permission Denied.')
        except discord.ext.commands.errors.BadArgument:
            await ctx.send('User Not Found')

    @commands.command()
    async def game(self, ctx,*, game):
        "Sets Bot's Game"
        if ctx.author.id == 422181415598161921:
            await self.bot.change_presence(activity=discord.Game(name=game))
            await ctx.send('Game set to : Playing ' + game)
        else:
            await ctx.send('Invalid Permissions')


    @commands.command()
    async def create_role(self,ctx,color="white",perms=0,*, name="new role"):
        '''Creates a Role'''
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send("Invalid Permissions")
        permissions= discord.Permissions(permissions=int(perms))
        hex = matplotlib.colors.cnames[color]
        hex1 = hex[1:]
        hex2 = int(hex1, 16)
        colour = discord.Color(hex2)
        await ctx.guild.create_role(name=name,permissions=permissions,color=colour)
        await ctx.send(f"Role {name} was created with permissions: {perms} and color: {color}")


    @commands.command()
    async def botname(self, ctx, nickname: str):
        'Changes Bot Nickname'
        if ctx.author.id == 422181415598161921:
            me = ctx.me
            await me.edit(nick=nickname)
            await ctx.send('Nickname set to {}'.format(nickname))
        else:
            await ctx.send("Invalid Permissions")


    @commands.command()
    async def annoy(self,ctx):
        '''Sends a link to my webserver'''
        await ctx.send("https://annoycapn.herokuapp.com/index/")




def setup(bot):
    bot.add_cog(Regular(bot))