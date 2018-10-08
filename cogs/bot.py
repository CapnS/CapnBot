import discord
from discord.ext import commands
import psutil
import time
import inspect
import os
import dweepy 
import git 
from .paginator import HelpPaginator, CannotPaginate

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

    @commands.command(aliases=["about"])
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
        uptime = self.get_uptime(brief=True)
        for guild in self.bot.guilds:
            all_guilds.append(guild)
        total_members = sum(1 for _ in self.bot.get_all_members())
        capn = await self.bot.get_user_info(422181415598161921)
        dir_path = os.path.dirname(os.path.realpath(__file__))
        dir_path = os.path.dirname(dir_path)
        try:
            repo = git.Repo(dir_path)
        except:
            repo = git.Repo(r"/home/zachary/CapnBot.git")
        print(dir_path)
        commit = repo.head.commit.message    
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
        em.add_field(name="Latest Commit",value = f"```css\n{commit}\n```")
        em.set_footer(text='Requested by '+ctx.author.name, icon_url=ctx.author.avatar_url)
        em.set_thumbnail(url=self.bot.user.avatar_url)
        await ctx.send(content=None, embed=em)

    @commands.command()
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
    async def stats(self,ctx,command=None):
        if command:
            data = await self.bot.db.fetchrow("SELECT * FROM commands WHERE command_name=$1;",command)
            if data == None:
                return await ctx.send("Not a valid command")
            uses = data["uses"]
            return await ctx.send(f"{command} has {uses} uses")
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

    @commands.command(name='help')
    async def _help(self, ctx, *, command: str = None):
        """Shows help about a command or the bot"""

        try:
            if command is None:
                p = await HelpPaginator.from_bot(ctx)
            else:
                entity = self.bot.get_cog(command) or self.bot.get_command(command)

                if entity is None:
                    clean = command.replace('@', '@\u200b')
                    return await ctx.send(f'Command or category "{clean}" not found.')
                elif isinstance(entity, commands.Command):
                    p = await HelpPaginator.from_command(ctx, entity)
                else:
                    p = await HelpPaginator.from_cog(ctx, entity)

            await p.paginate()
        except Exception as e:
            await ctx.send(e)

def setup(bot):
    bot.add_cog(BotInfo(bot))