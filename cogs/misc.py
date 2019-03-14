import discord
from discord.ext import commands
import bs4
from twilio.rest import Client
import urllib.request
import html
import matplotlib
import io
import textwrap
import traceback
from contextlib import redirect_stdout
import time
import aiohttp
#import language_check as lc
from selenium import webdriver
from pyvirtualdisplay import Display

class Plural:
    def __init__(self, **attr):
        iterator = attr.items()
        self.name, self.value = next(iter(iterator))

    def __str__(self):
        v = self.value
        if v == 0 or v > 1:
            return f'{v} {self.name}s'
        return f'{v} {self.name}'

def human_join(seq, delim=', ', final='or'):
    size = len(seq)
    if size == 0:
        return ''
    if size == 1:
        return seq[0]
    if size == 2:
        return f'{seq[0]} {final} {seq[1]}'

    return delim.join(seq[:-1]) + f' {final} {seq[-1]}'

class TabularData:
    def __init__(self):
        self._widths = []
        self._columns = []
        self._rows = []

    def set_columns(self, columns):
        self._columns = columns
        self._widths = [len(c) + 2 for c in columns]

    def add_row(self, row):
        rows = [str(r) for r in row]
        self._rows.append(rows)
        for index, element in enumerate(rows):
            width = len(element) + 2
            if width > self._widths[index]:
                self._widths[index] = width

    def add_rows(self, rows):
        for row in rows:
            self.add_row(row)

    def render(self):
        sep = '+'.join('-' * w for w in self._widths)
        sep = f'+{sep}+'

        to_draw = [sep]

        def get_entry(d):
            elem = '|'.join(f'{e:^{self._widths[i]}}' for i, e in enumerate(d))
            return f'|{elem}|'

        to_draw.append(get_entry(self._columns))
        to_draw.append(sep)

        for row in self._rows:
            to_draw.append(get_entry(row))

        to_draw.append(sep)
        return '\n'.join(to_draw)

class Misc():

    def __init__(self, bot):
        self.bot = bot
        self._last_result = None
        #self.g = lc.LanguageTool("en-US")

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])

        # remove `foo`
        return content.strip('` \n')

    @commands.command()
    async def echo(self, ctx, *, repeat):
        await ctx.send(repeat)

    @commands.command()
    async def eval(self, ctx, *, body: str):
        """Evaluates a code"""
        if not ctx.author.id == 422181415598161921:
            return
        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
            '_': self._last_result
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction('\u2705')
            except:
                pass

            if ret is None:
                if value:
                    await ctx.send(f'```py\n{value}\n```')
            else:
                self._last_result = ret
                await ctx.send(f'```py\n{value}{ret}\n```')
    @commands.command()
    async def embed(self, ctx, color_name, *, user_input):
        '-> Embeds a message' 
        try:
            embed = discord.Embed(title=user_input, color = int(color_name,16))
            return await ctx.send(embed=embed)
        except:
            pass
        try:
            hex = matplotlib.colors.cnames[color_name]
        except:
            return await ctx.send("Not a valid color")
        hex1 = hex[1:]
        hex2 = int(hex1, 16)
        embed = discord.Embed(title=user_input, color = hex2)
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    async def sql(self, ctx, *, query: str):
        """Run some SQL."""
        if not ctx.author.id == 422181415598161921:
            return
        query = self.cleanup_code(query)

        is_multistatement = query.count(';') > 1
        if is_multistatement:
            # fetch does not support multiple statements
            strategy = self.bot.db.execute
        else:
            strategy = self.bot.db.fetch

        try:
            start = time.perf_counter()
            results = await strategy(query)
            dt = (time.perf_counter() - start) * 1000.0
        except Exception:
            return await ctx.send(f'```py\n{traceback.format_exc()}\n```')

        rows = len(results)
        if is_multistatement or rows == 0:
            return await ctx.send(f'`{dt:.2f}ms: {results}`')

        headers = list(results[0].keys())
        table = TabularData()
        table.set_columns(headers)
        table.add_rows(list(r.values()) for r in results)
        render = table.render()

        fmt = f'```\n{render}\n```\n*Returned {Plural(row=rows)} in {dt:.2f}ms*'
        if len(fmt) > 2000:
            fp = io.BytesIO(fmt.encode('utf-8'))
            await ctx.send('Too many results...', file=discord.File(fp, 'results.txt'))
        else:
            await ctx.send(fmt)

    @commands.command()
    async def embed_colors(self,ctx):
        '''Shows all possible colors for the Embed command'''
        all_colors = []
        msg = ""
        for color in matplotlib.colors.cnames.keys():
            all_colors.append(color)
        for color in all_colors:
            msg = f"{msg}, {color}"
        await ctx.send(f"``{msg}``")


    @commands.command()
    async def pin(self, ctx):
        'Pins last message'
        await ctx.message.delete()
        if ctx.author.guild_permissions.administrator:
            async for message in ctx.channel.history(limit=1):
                await message.pin()

    '''
    @commands.command()
    async def grammar(self,ctx,*,sentence):
        def go():
            matches = self.g.check(sentence)
            correction = lc.correct(sentence,matches)
            return matches, correction
        matches, correction = await self.bot.loop.run_in_executor(None,go)
        red = discord.Color.red()
        em = discord.Embed(title="Grammar Checker",description = str(len(matches)) + " error(s)", color = red)
        em.add_field(name = "Before",value = "```" + sentence + "```",inline=False)
        em.add_field(name = "After", value = "```" + correction + "```",inline=False)
        em.set_footer(text="Requested by "+ str(ctx.author))
        await ctx.send(embed=em)
    '''

    @commands.command()
    async def text(self, ctx,*, message):
        'Texts Me'
        message = message + " - " + str(ctx.author)
        data = await self.bot.db.fetchrow("SELECT * FROM keys;")
        account_sid=data["sid"]
        auth_token=data["twilio_token"]
        client = Client(account_sid, auth_token)
        message = client.messages.create(to='+17133928748', from_='+18329003495', body=str(message))
        await ctx.send("Your Message has been Sent.")

    @commands.command()
    async def avatar(self,ctx,user:discord.Member=None):
        if not user:
            user = ctx.author
        yellow = discord.Color.gold()
        em = discord.Embed(title="Avatar URL",url = user.avatar_url,color=yellow)
        em.set_image(url=user.avatar_url)
        await ctx.send(embed=em)


    @commands.command()
    async def donate(self, ctx):
        '''Sends a link to donate to me'''
        await ctx.send('https://paypal.me/trgcapn\nhttps://www.patreon.com/capn')

    @commands.command()
    async def updatedonors(self, ctx, amount:float, *, name):
        data = await self.bot.db.fetch("SELECT * from donors WHERE name = $1;",name)
        if not data:
            await self.bot.db.execute("INSERT INTO donors VALUES ($1, $2);",name,amount)
            return await ctx.send(f"Added {name} to Donor List")
        else:
            previous = data["amount"]
            current = previous + amount
            await self.bot.db.execute("UPDATE donors SET amount=$1 WHERE name=$2;",current,name)
            return await ctx.send(f"Updated {name}'s Donation amount to ${current}")


    @commands.command()
    async def donors(self, ctx):
        '''Shows a  list of Donors'''
        data = await self.bot.db.fetch("SELECT * FROM donors;")
        msg = ""
        for donor in data:
            donor_name = donor["name"]
            amount = donor["amount"]
            msg = f"{msg}\n {donor_name}-${amount}"
        em = discord.Embed()
        em.add_field(name='All Donors', value=msg)
        await ctx.send(content=None, embed=em)

    @commands.command()
    async def chucknorris(self,ctx):
        async with aiohttp.ClientSession() as session:
            async with session.get("http://api.icndb.com/jokes/random") as resp:
                data = await resp.json()
                value = data.get("value")
                joke = value.get("joke")
                await ctx.send(joke)

    @commands.command()
    async def joke(self, ctx):
        async with aiohttp.ClientSession() as session:
            headers ={"Accept":"application/json"}
            async with session.get("https://icanhazdadjoke.com/",headers=headers) as resp:
                data = await resp.json()
                joke = data.get("joke")
                await ctx.send(joke)

    @commands.command()
    async def track_users(self, ctx):
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send("You have to be an administrator to use this command")
        data = await self.bot.db.fetchrow("SELECT * from tracked_channels WHERE guild_id = $1;", ctx.guild.id)
        if data:
            try:
                channel = ctx.guild.get_channel(data['channel_id'])
                if not channel:
                    pass
                else:
                    return await ctx.send("Your guild members are already being tracked")
            except:
                pass
        members = str(len(ctx.guild.members))
        try:
            overwrite = {
                guild.default_role: discord.PermissionOverwrite(connect=False)
                }
            channel = await ctx.guild.create_text_channel(
                "User Count: "+ members,
                overwrite
                )
        except discord.errors.Forbidden:
            return await ctx.send("The bot does not have permissions to make a new channel")
        await self.bot.db.execute("INSERT INTO tracked_channels VALUES ($1, $2);', ctx.guild.id, channel.id)
            
def setup(bot):
    bot.add_cog(Misc(bot))
