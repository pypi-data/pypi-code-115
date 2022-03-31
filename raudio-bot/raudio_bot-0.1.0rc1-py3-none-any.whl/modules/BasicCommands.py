import os

from dataclasses import asdict
from unicodedata import name

from discord.ext import commands

# from raudio.config import raudio_config_from_json

class BasicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        """Test that Raudio is working"""
        await ctx.send("Pong!")

    @commands.command()
    async def config(self, ctx):
        """Print your current configuration settings"""
        config = asdict(self.bot.config)

        # Filter out underscore properties
        config = dict((filter(lambda k: not k[0].startswith('_'), config.items())))

        await ctx.send(f"Your current config is: {config}")

    @commands.command()
    async def reload(self, ctx):
        """Reload the current commands (for developers)"""
        self.bot.reload_modules()
        await ctx.send("Reloading commands...")

#       FIXME: Import currently not working
#        if self.bot.config._config_file_path:
#            await ctx.send("Reloading configuration file...")
#            self.bot.config = raudio_config_from_json(self.bot.config._config_file_path)


def setup(bot: commands.Bot):
    bot.add_cog(BasicCommands(bot))
