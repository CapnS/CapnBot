import discord
from discord.ext import commands

class Roles(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def role(self, ctx):
        'Gets Top Role'
        await ctx.send(ctx.author.top_role)

    @commands.command()
    async def giverole(self, ctx, user: discord.Member, roles):
        'Gives user a role'
        try:
            if ctx.author.guild_permissions.administrator:
                role = discord.utils.get(user.guild.roles, name=roles)
                await user.add_roles(role)
                await ctx.send(('Gave {}'.format(user.name) + ' the role: ') + roles)
            else:
                return await ctx.send('Permission Denied.')
        except:
            ctx.send('User Not Found')
    '''
    @commands.command()
    async def streamer(self, ctx):
        '-> gives the role of streamer'
        if (not (str(ctx.author.top_role) == 'Streamer')):
            role = discord.utils.get(user.guild.roles, name='Streamers')
            await ctx.author.add_roles(role)
            role = discord.utils.get(user.guild.roles, name='Member')
            await ctx.author.remove_roles(role)

    @commands.command()
    async def accept(self, ctx):
        "-> For user's to accept rules"
        role = discord.utils.get(user.guild.roles, name='Member')
        await ctx.author.add_roles(role)
        role = discord.utils.get(user.guild.roles, name='Prospective')
        await ctx.author.remove_roles(role)
    '''

    @commands.command()
    async def remove(self, ctx, roles, user: discord.Member):
        'Removes a role'
        if ctx.author.guild_permissions.administrator:
            role = discord.utils.get(user.guild.roles, name=roles)
            await user.remove_roles(role)
            await ctx.send(('Took away ' + roles) + ' from {}'.format(user.name))
        else:
            return await ctx.send('Permission Denied.')

def setup(bot):
    bot.add_cog(Roles(bot))