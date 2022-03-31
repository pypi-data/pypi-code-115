import asyncio
import time

import discord
import requests
from discord.ext import commands

ffmpeg_options = {"options": "-vn"}


async def from_url(url, *, loop=None, stream=False):
    return discord.FFmpegPCMAudio(url, **ffmpeg_options)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """Joins a voice channel"""
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @commands.command()
    async def play(self, ctx):
        """Resumes playing of stream"""

        if ctx.message.author.id in self.bot.config.authenticated:
            # TODO PUT request to /play
            r = requests.put(self.bot.config.stream_url + "/play")
            await ctx.send("Resuming stream")
        else:
            # DO nothing (non auth user)
            await ctx.send("You are not able to do that")

    @commands.command()
    async def pause(self, ctx):
        """Pauses stream"""

        if ctx.message.author.id in self.bot.config.authenticated:
            # TODO PUT request to /pause
            r = requests.put(self.bot.config.stream_url + "/pause")
            await ctx.send("Pausing stream")
        else:
            # DO nothing (non auth user)
            await ctx.send("You are not able to do that")

    @commands.command()
    async def skip(self, ctx):
        """Resumes playing of stream"""

        if ctx.message.author.id in self.bot.config.authenticated:
            # TODO PUT request to /skip
            r = requests.put(self.bot.config.stream_url + "/skip")
            await ctx.send("Playing next song")
        else:
            # DO nothing (non auth user)
            await ctx.send("You are not able to do that")
        time.sleep(3)

    async def fetch_next_song(self, event, ctx):
        player = await from_url(
            self.bot.config.stream_url, loop=self.bot.loop, stream=True
        )
        ctx.voice_client.play(
            player, after=lambda e: print(f"Player error: {e}") if e else event.set()
        )

    async def play_songs(self, ctx):
        while True:
            print("playing song")
            event = asyncio.Event()
            await self.fetch_next_song(event, ctx)
            await event.wait()

    @commands.command()
    async def listen(self, ctx):
        """Streams from server"""
        await self.play_songs(ctx)
        await ctx.send(f"Now playing Raudio Mix")

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""

        await ctx.voice_client.disconnect()

    @listen.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()


def setup(bot: commands.Bot):
    bot.add_cog(Music(bot))
