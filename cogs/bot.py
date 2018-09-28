import discord
from discord.ext import commands
import psutil
import time
import inspect
import os

class BotInfo():
    def __init__(self,bot):
        self.bot=bot
        self.process = psutil.Process()

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])
        return content.strip('` \n')
        
    @commands.command()
    async def suggest(self,ctx,*,suggestion):
        '''dms me a suggestion'''
        dweepy.dweet_for('CapnBot',{"msg":suggestion})
        await ctx.send("Your suggestion has been sent.")
    
    def get_uptime(self, *, brief=False):
        now = time.time()
        delta = now - self.bot.launch_time
        (hours, remainder) = divmod(int(delta), 3600)
        (minutes, seconds) = divmod(remainder, 60)
        (days, hours) = divmod(hours, 24)
        if (not brief):
            if days:
                fmt = '{d} days, {h} hours, {m} minutes, and {s} seconds'
            else:
                fmt = '{h} hours, {m} minutes, and {s} seconds'
        else:
            fmt = '{h}h {m}m {s}s'
            if days:
                fmt = '{d}d ' + fmt
        return fmt.format(d=days, h=hours, m=minutes, s=seconds)

    @commands.command()
    @commands.guild_only()
    async def botinfo(self, ctx):
        'Gives Bot Info'
        prefixes = await self.bot.db.fetchrow("SELECT * FROM prefixes WHERE guild_id=$1",ctx.guild.id)
        if prefixes == None:
            prefix = "c!"
        else:
            prefix = prefixes["prefix"]
        me = ctx.me
        all_guilds = []
        memory_usage = self.process.memory_full_info().uss / (1024 ** 2)
        cpu_usage = self.process.cpu_percent() / psutil.cpu_count()
        uptime = self.get_uptime(brief=True)
        for guild in self.bot.guilds:
            all_guilds.append(guild)
        total_members = sum(1 for _ in self.bot.get_all_members())
        capn = await self.bot.get_user_info(422181415598161921)        
        em = discord.Embed(title = "Bot Info", description = f"[Bot Invite](https://discordapp.com/oauth2/authorize?&client_id={self.bot.user.id}&scope=bot&permissions=8) | [Support Server](https://discord.gg/MJV4qsV) | [Source Code](https://github.com/CapnS/CapnBot)")
        em.color = discord.Color.gold()
        em.add_field(name='Bot Name', value=str(me.display_name))
        em.add_field(name='Guilds', value=str(len(all_guilds)))
        em.add_field(name = "Users", value = str(total_members))
        em.add_field(name='Commands Run', value=str(self.bot.counter))
        em.add_field(name='Process Stats', value=f'''{memory_usage:.2f} MiB\n{psutil.cpu_percent()}% CPU''')
        em.add_field(name='Uptime', value=uptime)
        em.add_field(name = "Prefixes", value = f"``{prefix}``")
        em.add_field(name="Coded By", value = capn.mention)
        em.set_footer(text='Requested by '+ctx.author.name, icon_url=ctx.author.avatar_url)
        em.set_thumbnail(url=self.bot.user.avatar_url)
        await ctx.send(content=None, embed=em)

    @commands.command(aliases=['sauce', 'sawce'])
    async def source(self, ctx, command: str = None):
        """Get the bot's source link for a command or the whole source"""

        source_url = "https://github.com/CapnS/CapnBot"
        if command is None:
            return await ctx.send(source_url)
        

        obj = self.bot.get_command(command.replace('.', ' '))
        if obj is None:
            return await ctx.send('Could not find command.')

        src = obj.callback.__code__
        lines, firstlineno = inspect.getsourcelines(src)
        if not obj.callback.__module__.startswith('discord'):
            location = os.path.relpath(src.co_filename).replace('\\', '/')
        else:
            location = obj.callback.__module__.replace('.', '/') + '.py'
            source_url = "https://github.com/Zeniath/Non-Don-Tools"

        await ctx.send(f"<{source_url}/tree/master/{location}/#L{firstlineno}-L{firstlineno + len(lines) - 1}>")

    @commands.command()
    async def stats(self,ctx):
        data = await self.bot.db.fetch("SELECT * FROM commands ORDER BY uses DESC LIMIT 10;")
        leaderboard = ""
        i=1
        for row in data:
            command, uses = row["command_name"], row["uses"]
            leaderboard = f"{leaderboard} {i} - {command} : {uses} uses \n"
            i+=1
        color= discord.Color.blurple()
        em = discord.Embed(title="Command Usage", description=leaderboard)
        em.color=(color)
        await ctx.send(embed=em)

    async def change_message(self,author,message,i):
        if i == 0:
            cog = self.bot.cogsList[0]
            commands = self.bot.comsDict["No Cogs"]
        else:
            cog = self.bot.cogsList[i]
            commands = self.bot.comsDict[cog]
        em = discord.Embed(title = "Help", description = cog)
        for com in commands:
            em.add_field(name=com.signature,value=com.help,inline=False)
        await message.edit(embed=em)
        def check(reaction, user):
            return user == author and reaction.emoji in ('\U000025c0', '\U000025b6')
        reaction, user = await self.bot.wait_for("reaction_add",check=check,timeout=60)
        try:
            await message.remove_reaction(reaction.emoji,user)
        except:
            pass
        if reaction.emoji == '\U000025c0':
            if i == 0:
                i=10
                await self.change_message(author,message,i)
            else:
                i-=1
                await self.change_message(author,message,i)
        if reaction.emoji == '\U000025b6':
            if i == 10:
                i=0
                await self.change_message(author,message,i)
            else:
                i+=1
                await self.change_message(author,message,i)

        
    @commands.command()
    async def help(self,ctx, command=None):
        '''Shows this message'''
        self.bot.comsDict = {}
        self.bot.cogsList = []
        self.bot.no_cogs = []
        author = ctx.author
        i=0
        if command == None:
            for com in self.bot.commands:
                if com.cog_name == None:
                    self.bot.no_cogs.append(com)
                if com.cog_name in self.bot.cogsList:
                    pass
                else:
                    self.bot.comsDict.update({com.cog_name:self.bot.get_cog_commands(com.cog_name)})
                    self.bot.cogsList.append(com.cog_name)
            try:
                self.bot.comsDict.update({"No Cogs":self.bot.no_cogs})
                self.bot.cogsList.append("No Cogs")
                cog = self.bot.cogsList[0]
                commands = self.bot.comsDict["No Cogs"]
                em = discord.Embed(title = "Help", description = cog)
                for com in commands:
                    em.add_field(name=com.signature,value=com.help,inline=False)
                help_message = await ctx.send(embed=em)
                await help_message.add_reaction("\U000025c0")
                await help_message.add_reaction("\U000025b6")
                def check(reaction, user):
                    return user == ctx.author and reaction.emoji in ('\U000025c0', '\U000025b6')
                reaction,user = await self.bot.wait_for("reaction_add",check=check)
                try:
                    await help_message.remove_reaction(reaction,user)
                except:
                    pass
                if reaction.emoji == '\U000025c0':
                    if i == 0:
                        i= 10
                        await self.change_message(author,help_message,i)
                    else:
                        i-=1
                        await self.change_message(author,help_message,i)
                if reaction.emoji == '\U000025b6':
                    if i == 10:
                        i=0
                        await self.change_message(author,help_message,i)
                    else:
                        i+=1
                        await self.change_message(author,help_message,i)
            except KeyError:
                pass        
        if command != None:
            command = self.bot.get_command(command)
            await ctx.send("``"+command.signature+"``")

def setup(bot):
    bot.add_cog(BotInfo(bot))