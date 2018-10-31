import discord
from discord.ext import commands
import datetime
import asyncio
import itertools
import sys
import traceback
from async_timeout import timeout
from functools import partial
from youtube_dl import YoutubeDL


ytdlopts = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # ipv6 addresses cause issues sometimes
}

ffmpegopts = {
    'before_options': '-nostdin',
    'options': '-vn'
}

ytdl = YoutubeDL(ytdlopts)


class VoiceConnectionError(commands.CommandError):
    """Custom Exception class for connection errors."""


class InvalidVoiceChannel(VoiceConnectionError):
    """Exception for cases of invalid Voice Channels."""


class YTDLSource(discord.PCMVolumeTransformer):

    def __init__(self, source, *, data, requester):
        super().__init__(source)
        self.requester = requester
        self.date = data.get('upload_date')
        self.thumbnail = data.get('thumbnail') 
        self.duration = data.get("duration") 
        self.uploader = data.get("uploader")
        self.title = data.get('title')
        self.web_url = data.get('webpage_url')
        
        # YTDL info dicts (data) have other useful information you might want
        # https://github.com/rg3/youtube-dl/blob/master/README.md

    def __getitem__(self, item: str):
        """Allows us to access attributes similar to a dict.
        This is only useful when you are NOT downloading.
        """
        return self.__getattribute__(item)

    @classmethod
    async def create_source(cls, ctx, search: str, *, loop, download=False):
        loop = loop or asyncio.get_event_loop()

        to_run = partial(ytdl.extract_info, url=search, download=download)
        data = await loop.run_in_executor(None, to_run)

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        await ctx.send(f'```ini\n[Added {data["title"]} to the Queue.]\n```', delete_after=15)

        if download:
            source = ytdl.prepare_filename(data)
        else:
            return {'webpage_url': data['webpage_url'], 'requester': ctx.author, 'title': data['title']}

        return cls(discord.FFmpegPCMAudio(source), data=data, requester=ctx.author)

    @classmethod
    async def regather_stream(cls, data, *, loop):
        """Used for preparing a stream, instead of downloading.
        Since Youtube Streaming links expire."""
        loop = loop or asyncio.get_event_loop()
        requester = data['requester']

        to_run = partial(ytdl.extract_info, url=data['webpage_url'], download=False)
        data = await loop.run_in_executor(None, to_run)
        
        return cls(discord.FFmpegPCMAudio(data['url']), data=data, requester=requester)


class MusicPlayer:
    __slots__ = ('bot', '_guild', '_channel', '_cog', 'queue', 'next', 'current', 'np', 'volume')

    def __init__(self, ctx):
        self.bot = ctx.bot
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        self.np = None  # Now playing message
        self.volume = .5
        self.current = None

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        """Our main player loop."""
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                # Wait for the next song. If we timeout cancel the player and disconnect...
                async with timeout(300):  # 5 minutes...
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                return self.destroy(self._guild)

            if not isinstance(source, YTDLSource):
                # Source was probably a stream (not downloaded)
                # So we should regather to prevent stream expiration
                try:
                    source = await YTDLSource.regather_stream(source, loop=self.bot.loop)
                except Exception as e:
                    await self._channel.send(f'There was an error processing your song.\n'
                                             f'```css\n[{e}]\n```')
                    continue

            source.volume = self.volume
            self.current = source
            self._guild.voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
            volume = str(source.volume * 100)
            (hours,remainder)= divmod(int(source.duration),3600)
            (minutes,seconds)= divmod(remainder,60)
            if seconds < 10:
                seconds = ("0"+str(seconds))
            if hours:
                fmt = '{h}:{m}:{s}'
            else:
                (minutes,seconds) = divmod(int(source.duration), 60)
                if seconds < 10:
                    seconds = ("0"+str(seconds))
                fmt = '{m}:{s}'
            duration = fmt.format(h=hours,m=minutes,s=seconds)
            date = source.date[4:6]+"/"+source.date[6:8]+"/"+source.date[:4]
            em = discord.Embed(title = "Song Details",description = source.title,timestamp = datetime.datetime.utcnow())
            em.add_field(name = ":microphone:Duration",value = duration)
            em.add_field(name = ":calling:Uploader",value = source.uploader)
            em.add_field(name = ":calendar:Uploaded on",value = date)
            em.add_field(name = ":selfie:Requested by", value = source.requester)
            em.add_field(name = ":headphones:Volume",value = f"{volume}%")
            em.add_field(name = ":link:Song URL", value =f"[URL]({source.web_url})")
            em.set_thumbnail(url=source.thumbnail)

            self.np = await self._channel.send(embed = em)
            await self.next.wait()

            # Make sure the FFmpeg process is cleaned up.
            source.cleanup()
            self.current = None

            try:
                # We are no longer playing this song...
                await self.np.delete()
            except discord.HTTPException:
                pass

    def get_np(self):
        return self.np

    def destroy(self, guild):
        """Disconnect and cleanup the player."""
        return self.bot.loop.create_task(self._cog.cleanup(guild))


class Music:
    """Music related commands."""

    __slots__ = ('bot', 'players', 'votes','np')

    def __init__(self, bot):
        self.bot = bot
        self.players = {}
        self.votes = []
        self.np = MusicPlayer.get_np()

    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            del self.players[guild.id]
        except KeyError:
            pass

    async def __local_check(self, ctx):
        """A local check which applies to all commands in this cog."""
        if not ctx.guild:
            raise commands.NoPrivateMessage
        return True

    async def __error(self, ctx, error):
        """A local error handler for all errors arising from commands in this cog."""
        if isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.send('This command can not be used in Private Messages.')
            except discord.HTTPException:
                pass
        elif isinstance(error, InvalidVoiceChannel):
            await ctx.send('Error connecting to Voice Channel. '
                           'Please make sure you are in a valid channel or provide me with one')
        elif isinstance(error, commands.errors.CheckFailure):
            if ctx.message.content.startswith("!stop"):
                return await ctx.send("You do not have the DJ role. Please create a role named 'DJ' to use this command.")

    def get_player(self, ctx):
        """Retrieve the guild player, or generate one."""
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = MusicPlayer(ctx)
            self.players[ctx.guild.id] = player

        return player

    @commands.command(name='connect', aliases=['join'])
    async def join(self, ctx, *, channel: discord.VoiceChannel=None):
        """Connect to voice.
        """
        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                raise InvalidVoiceChannel('No channel to join. Please either specify a valid channel or join one.')

        vc = ctx.voice_client

        if vc:
            if vc.channel.id == channel.id:
                return
            try:
                await vc.move_to(channel)
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f'Moving to channel: <{channel}> timed out.')
        else:
            try:
                await channel.connect()
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f'Connecting to channel: <{channel}> timed out.')

        await ctx.send(f'Connected to: **{channel}**', delete_after=20)

    @commands.command(name='play', aliases=['sing'])
    async def play(self, ctx, *, search: str):
        """Request a song and add it to the queue.
        """
        await ctx.trigger_typing()

        vc = ctx.voice_client

        if not vc:
            await ctx.invoke(self.join)

        player = self.get_player(ctx)

        # If download is False, source will be a dict which will be used later to regather the stream.
        # If download is True, source will be a discord.FFmpegPCMAudio with a VolumeTransformer.
        source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop, download=False)

        await player.queue.put(source)

    @commands.command(name='pause')
    async def pause(self, ctx):
        """Pause the currently playing song."""
        vc = ctx.voice_client

        if not vc or not vc.is_playing():
            return await ctx.send('I am not currently playing anything!', delete_after=20)
        elif vc.is_paused():
            return

        vc.pause()
        await ctx.send(f'**`{ctx.author}`**: Paused the song!')

    @commands.command(name='resume')
    async def resume(self, ctx):
        """Resume the currently paused song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('I am not currently playing anything!', delete_after=20)
        elif not vc.is_paused():
            return

        vc.resume()
        await ctx.send(f'**`{ctx.author}`**: Resumed the song!')

    @commands.command(name='skip')
    async def skip(self, ctx):
        """Skip the song."""
        vc = ctx.voice_client
        requester = vc.source.requester
        voter = ctx.message.author
        if not vc or not vc.is_connected():
            return await ctx.send('I am not currently playing anything!', delete_after=20)
        if vc.is_paused():
            pass
        elif not vc.is_playing():
            return
        for role in voter.roles:
            if role.name == "DJ":
                await ctx.send("DJ asked to skip song, now skipping.")
                self.votes = []
                vc.stop()
                return
        if voter == requester:
            await ctx.send("Requester asked to skip song, now skipping.")
            self.votes = []
            vc.stop()         
        elif voter not in self.votes:
            self.votes.append(voter)
            total_votes = len(self.votes)
            if total_votes >= 3:
                await ctx.send('Skip vote passed, skipping song...')
                self.votes = []
                vc.stop()
            else:
                await ctx.send('Skip vote added, currently at [{}/3]'.format(str(total_votes)))
        else:
            await ctx.send("You have already voted to skip this song!")

    @commands.command(name='queue', aliases=['q', 'playlist'])
    async def queue(self, ctx):
        """Retrieve a basic queue of upcoming songs."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('I am not currently connected to voice!', delete_after=20)

        player = self.get_player(ctx)
        if player.queue.empty():
            return await ctx.send('There are currently no more queued songs.')

        # Grab up to 5 entries from the queue...
        upcoming = list(itertools.islice(player.queue._queue, 0, 5))

        fmt = '\n'.join(f'**`{_["title"]}`**' for _ in upcoming)
        embed = discord.Embed(title=f'Upcoming - Next {len(upcoming)}', description=fmt)

        await ctx.send(embed=embed)

    @commands.command(name='now_playing', aliases=['np', 'current', 'currentsong', 'playing'])
    async def playing(self, ctx):
        """Display information about the currently playing song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('I am not currently connected to voice!', delete_after=20)

        source = vc.source

        player = self.get_player(ctx)
        if not player.current:
            return await ctx.send('I am not currently playing anything!')

        try:
            # Remove our previous now_playing message
            await self.np.delete()
        except discord.HTTPException:
            pass

        volume = str(source.volume * 100)
        (hours,remainder)= divmod(int(source.duration),3600)
        (minutes,seconds)= divmod(remainder,60)
        if seconds < 10:
            seconds = ("0"+str(seconds))
        if hours:
            fmt = '{h}:{m}:{s}'
        else:
            (minutes,seconds) = divmod(int(source.duration), 60)
            if seconds < 10:
                seconds = ("0"+str(seconds))
            fmt = '{m}:{s}'
        duration = fmt.format(h=hours,m=minutes,s=seconds)
        date = source.date[4:6]+"/"+source.date[6:8]+"/"+source.date[:4]
        em = discord.Embed(title = "Song Details",description = source.title,timestamp = datetime.datetime.utcnow())
        em.add_field(name = ":microphone:Duration",value = duration)
        em.add_field(name = ":calling:Uploader",value = source.uploader)
        em.add_field(name = ":calendar:Uploaded on",value = date)
        em.add_field(name = ":selfie:Requested by", value = source.requester)
        em.add_field(name = ":headphones:Volume",value = f"{volume}%")
        em.add_field(name = ":link:Song URL", value = "[URL](source.web_url)")
        em.set_thumbnail(url=source.thumbnail)
        self.np = await ctx.send(embed = em)

    @commands.command(name='volume', aliases=['vol'])
    async def volume(self, ctx, *, vol: float):
        """Change the player volume.
        """
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            return await ctx.send('I am not currently connected to voice!', delete_after=20)

        if not 0 < vol < 101:
            return await ctx.send('Please enter a value between 1 and 100.')
        vol = round(vol,2)
        player = self.get_player(ctx)

        if vc.source:
            vc.source.volume = vol / 100

        player.volume = vol / 100
        await ctx.send(f'**`{ctx.author}`**: Set the volume to **{vol}%**')

    @commands.command(name='stop')
    async def stop(self, ctx):
        """Stop the currently playing song and destroy the player.
        """
        vc = ctx.voice_client
        voter = ctx.author
        if not vc or not vc.is_connected():
            return await ctx.send('I am not currently playing anything!', delete_after=20)
        for role in voter.roles:
            if role.name == "DJ":
                await ctx.send("DJ asked to stop the party, Lame!")
                await self.cleanup(ctx.guild)
                return
        await ctx.send("You must have the DJ Role to stop the Party!")
        


def setup(bot):
    bot.add_cog(Music(bot))

    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass
            
        try:
            for source in self.players[guild.id].queue._queue:
                source.cleanup()
        except KeyError:
            pass   
            
        try:
            del self.players[guild.id]
        except KeyError:
            pass    
