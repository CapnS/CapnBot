import random
import re
import json
from discord.ext import commands
import discord
from pyfiglet import figlet_format, FontError, FontNotFound
import urllib.parse
'Module for fun/meme commands commands'

class Fun():

    def __init__(self, bot):
        self.bot = bot
        self.regionals = {
            'a': '🇦',
            'b': '🇧',
            'c': '🇨',
            'd': '🇩',
            'e': '🇪',
            'f': '🇫',
            'g': '🇬',
            'h': '🇭',
            'i': '🇮',
            'j': '🇯',
            'k': '🇰',
            'l': '🇱',
            'm': '🇲',
            'n': '🇳',
            'o': '🇴',
            'p': '🇵',
            'q': '🇶',
            'r': '🇷',
            's': '🇸',
            't': '🇹',
            'u': '🇺',
            'v': '🇻',
            'w': '🇼',
            'x': '🇽',
            'y': '🇾',
            'z': '🇿',
            '0': '0⃣',
            '1': '1⃣',
            '2': '2⃣',
            '3': '3⃣',
            '4': '4⃣',
            '5': '5⃣',
            '6': '6⃣',
            '7': '7⃣',
            '8': '8⃣',
            '9': '9⃣',
            '!': '❗',
            '?': '❓',
        }
        self.emoji_reg = re.compile('<:.+?:([0-9]{15,21})>')
        self.ball = ['It is certain', 'It is decidedly so', 'Without a doubt', 'Yes definitely', 'You may rely on it', 'As I see it, yes', 'Most likely', 'Outlook good', 'Yes', 'Signs point to yes', 'Reply hazy try again', 'Ask again later', 'Better not tell you now', 'Cannot predict now', 'Concentrate and ask again', "Don't count on it", 'My reply is no', 'My sources say no', 'Outlook not so good', 'Very doubtful']
    emoji_dict = {
        'a': ['🇦', '🅰', '🍙', '🔼', '4⃣'],
        'b': ['🇧', '🅱', '8⃣'],
        'c': ['🇨', '©', '🗜'],
        'd': ['🇩', '↩'],
        'e': ['🇪', '3⃣', '📧', '💶'],
        'f': ['🇫', '🎏'],
        'g': ['🇬', '🗜', '6⃣', '9⃣', '⛽'],
        'h': ['🇭', '♓'],
        'i': ['🇮', 'ℹ', '🚹', '1⃣'],
        'j': ['🇯', '🗾'],
        'k': ['🇰', '🎋'],
        'l': ['🇱', '1⃣', '🇮', '👢', '💷'],
        'm': ['🇲', 'Ⓜ', '📉'],
        'n': ['🇳', '♑', '🎵'],
        'o': ['🇴', '🅾', '0⃣', '⭕', '🔘', '⏺', '⚪', '⚫', '🔵', '🔴', '💫'],
        'p': ['🇵', '🅿'],
        'q': ['🇶', '♌'],
        'r': ['🇷', '®'],
        's': ['🇸', '💲', '5⃣', '⚡', '💰', '💵'],
        't': ['🇹', '✝', '➕', '🎚', '🌴', '7⃣'],
        'u': ['🇺', '⛎', '🐉'],
        'v': ['🇻', '♈', '☑'],
        'w': ['🇼', '〰', '📈'],
        'x': ['🇽', '❎', '✖', '❌', '⚒'],
        'y': ['🇾', '✌', '💴'],
        'z': ['🇿', '2⃣'],
        ' ': ['▫'],
        '0': ['0⃣', '🅾', '0⃣', '⭕', '🔘', '⏺', '⚪', '⚫', '🔵', '🔴', '💫'],
        '1': ['1⃣', '🇮'],
        '2': ['2⃣', '🇿'],
        '3': ['3⃣'],
        '4': ['4⃣'],
        '5': ['5⃣', '🇸', '💲', '⚡'],
        '6': ['6⃣'],
        '7': ['7⃣'],
        '8': ['8⃣', '🎱', '🇧', '🅱'],
        '9': ['9⃣'],
        '?': ['❓'],
        '!': ['❗', '❕', '⚠', '❣'],
        'combination': [['cool', '🆒'], ['back', '🔙'], ['soon', '🔜'], ['free', '🆓'], ['end', '🔚'], ['top', '🔝'], ['abc', '🔤'], ['atm', '🏧'], ['new', '🆕'], ['sos', '🆘'], ['100', '💯'], ['loo', '💯'], ['zzz', '💤'], ['...', '💬'], ['ng', '🆖'], ['id', '🆔'], ['vs', '🆚'], ['wc', '🚾'], ['ab', '🆎'], ['cl', '🆑'], ['ok', '🆗'], ['up', '🆙'], ['10', '🔟'], ['11', '⏸'], ['ll', '⏸'], ['ii', '⏸'], ['tm', '™'], ['on', '🔛'], ['oo', '🈁'], ['!?', '⁉'], ['!!', '‼'], ['21', '📅']],
    }
    text_flip = {
        
    }
    char_list = "!#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}"
    alt_char_list = "{|}zʎxʍʌnʇsɹbdouɯlʞɾᴉɥƃɟǝpɔqɐ,‾^[\\]Z⅄XMΛ∩┴SɹQԀONW˥ʞſIHפℲƎpƆq∀@¿<=>;:68ㄥ9ϛㄣƐᄅƖ0/˙-'+*(),⅋%$#¡"[::(- 1)]
    for (idx, char) in enumerate(char_list):
        text_flip[char] = alt_char_list[idx]
        text_flip[alt_char_list[idx]] = char

    def has_dupe(duper):
        collect_my_duper = list(filter((lambda x: (x != '⃣')), duper))
        return len(set(collect_my_duper)) != len(collect_my_duper)

    def replace_combos(react_me):
        for combo in Fun.emoji_dict['combination']:
            if combo[0] in react_me:
                react_me = react_me.replace(combo[0], combo[1], 1)
        return react_me

    def replace_letters(react_me):
        for char in 'abcdefghijklmnopqrstuvwxyz0123456789!?':
            char_count = react_me.count(char)
            if char_count > 1:
                if len(Fun.emoji_dict[char]) >= char_count:
                    i = 0
                    while i < char_count:
                        if Fun.emoji_dict[char][i] not in react_me:
                            react_me = react_me.replace(char, Fun.emoji_dict[char][i], 1)
                        else:
                            char_count += 1
                        i += 1
            elif char_count == 1:
                react_me = react_me.replace(char, Fun.emoji_dict[char][0])
        return react_me

    @commands.command(aliases=['8ball'])
    async def ball8(self, ctx, *, msg: str):
        'plays 8 ball'
        answer = random.randint(0, 19)
        if True:
            if answer < 10:
                color = 32768
            elif 10 <= answer < 15:
                color = 16766720
            else:
                color = 16711680
            em = discord.Embed(color=color)
            em.add_field(name='❓ Question', value=msg)
            em.add_field(name='\ud83c\udfb1 8 ball', value=self.ball[answer], inline=False)
            await ctx.send(content=None, embed=em)
            try:
                await ctx_message.delete()
            except:
                pass
        else:
            await ctx.send('\ud83c\udfb1 ``{}``'.format(random.choice(self.ball)))

    @commands.command()
    async def vowelreplace(self, ctx, replace, *, msg):
        'Replaces all vowels in a word with a letter'
        result = ''
        for letter in msg:
            if letter.lower() in 'aeiou':
                result += replace
            else:
                result += letter
        try:
            await ctx.message.delete()
        except:
            await ctx.send(result)

    @commands.group(invoke_without_command=True)
    async def ascii(self, ctx, *, msg):
        'Convert text to ascii art'
        if ctx.invoked_subcommand is None:
            if msg:
                font = 'ascii_font'
                msg = str(figlet_format(msg.strip(), font='big'))
                if len(msg) > 2000:
                    await ctx.send('Message too long, RIP.')
                else:
                    try:
                        await ctx.message.delete()
                    except:
                        pass
                    await ctx.send('```\n{}\n```'.format(msg))
            else:
                await ctx.send('Please input text to convert to ascii art. Ex: ``>ascii stuff``')

    @commands.command()
    async def dice(self, ctx, *, msg='1'):
        'Roll dice.'
        try:
            await ctx.message.delete()
        except:
            pass
        invalid = 'Invalid syntax. Ex: `>dice 4` - roll four normal dice. `>dice 4 12` - roll four 12 sided dice.'
        dice_rolls = []
        dice_roll_ints = []
        try:
            (dice, sides) = re.split('[d\\s]', msg)
        except ValueError:
            dice = msg
            sides = '6'
        try:
            for roll in range(int(dice)):
                result = random.randint(1, int(sides))
                dice_rolls.append(str(result))
                dice_roll_ints.append(result)
        except ValueError:
            return await ctx.send(self.bot.bot_prefix + invalid)
        embed = discord.Embed(title='Dice rolls:', description=' '.join(dice_rolls))
        embed.add_field(name='Total:', value=sum(dice_roll_ints))
        await ctx.send('', embed=embed)

    @commands.command()
    async def textflip(self, ctx, *, msg):
        'Flip given text.'
        result = ''
        for char in msg:
            if char in self.text_flip:
                result += self.text_flip[char]
            else:
                result += char
        await ctx.send(result[::(- 1)])

    @commands.command()
    async def regional(self, ctx, *, msg):
        'Replace letters with regional indicator emojis'
        try:
            await ctx.message.delete()
        except:
            pass
        msg = list(msg)
        regional_list = [self.regionals[x.lower()] if x.isalnum() or (x in ['!', '?']) else x for x in msg]
        regional_output = '\u200b'.join(regional_list)
        await ctx.send(regional_output)

    @commands.command()
    async def space(self, ctx, *, msg):
        'Add n spaces between each letter.'
        try:
            await ctx.message.delete()
        except:
            pass
        if msg.split(' ', 1)[0].isdigit():
            spaces = int(msg.split(' ', 1)[0]) * ' '
            msg = msg.split(' ', 1)[1].strip()
        else:
            spaces = ' '
        spaced_message = spaces.join(list(msg))
        await ctx.send(spaced_message)

    @commands.command(aliases=['r'])
    async def react(self, ctx, msg: str, msg_id='last', channel='current', prefer_combine: bool=False):
        'Add letter(s) as reaction to previous message.'
        x=0
        msg = msg.lower()
        msg_id = None if (not msg_id.isdigit()) else int(msg_id)
        limit = 25 if msg_id else 1
        reactions = []
        non_unicode_emoji_list = []
        react_me = ''
        char_index = 0
        emotes = re.findall('<a?:(?:[a-zA-Z0-9]+?):(?:[0-9]+?)>', msg)
        react_me = re.sub('<a?:([a-zA-Z0-9]+?):([0-9]+?)>', '', msg)
        for emote in emotes:
            reactions.append(discord.utils.get(self.bot.emojis, id=int(emote.split(':')[(- 1)][:(- 1)])))
            non_unicode_emoji_list.append(emote)
        if Fun.has_dupe(non_unicode_emoji_list):
            return await ctx.send("You requested that I react with at least two of the exact same specific emoji. I'll try to find alternatives for alphanumeric text, but if you specify a specific emoji must be used, I can't help.")
        react_me_original = react_me
        if Fun.has_dupe(react_me):
            if prefer_combine:
                react_me = Fun.replace_combos(react_me)
            react_me = Fun.replace_letters(react_me)
            if Fun.has_dupe(react_me):
                if (not prefer_combine):
                    react_me = react_me_original
                    react_me = Fun.replace_combos(react_me)
                    react_me = Fun.replace_letters(react_me)
                    if Fun.has_dupe(react_me):
                        return await ctx.send('Failed to fix all duplicates. Cannot react with this string.')
                else:
                    return await ctx.send('Failed to fix all duplicates. Cannot react with this string.')
            lt_count = 0
            for char in react_me:
                if char not in '0123456789':
                    if char != '⃣':
                        reactions.append(char)
                else:
                    reactions.append(self.emoji_dict[char][0])
        else:
            lt_count = 0
            for char in react_me:
                if char in 'abcdefghijklmnopqrstuvwxyz0123456789!?':
                    reactions.append(self.emoji_dict[char][0])
                else:
                    reactions.append(char)
        if channel == 'current':
            async for message in ctx.channel.history(limit=2):
                if x == 0:
                    x+=1
                else:
                    for i in reactions:
                        try:
                            await message.add_reaction(i)
                        except:
                            for i in reactions:
                                await message.add_reaction(i)
                    await ctx.message.delete()
        else:
            found_channel = find_channel(ctx.guild.channels, channel)
            if (not found_channel):
                found_channel = find_channel(self.bot.get_all_channels(), channel)
            if found_channel:
                async for message in found_channel.history(limit=limit):
                    if ((not msg_id) and (message.id != ctx.message.id)) or (msg_id == message.id):
                        for i in reactions:
                            try:
                                await message.add_reaction(i)
                            except:
                                pass
            else:
                await ctx.send('Channel not found.')

def setup(bot):
    bot.add_cog(Fun(bot))