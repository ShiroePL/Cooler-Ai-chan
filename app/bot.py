import discord
from discord.ext import commands
from app.config import Config
import os
from app.utils.logger import logger

intents = discord.Intents.default()
intents.message_content = True


bot = commands.Bot(command_prefix='+', intents=discord.Intents.all())


@bot.event
async def on_ready():
    logger.info("------")
    logger.info("Cooler AI-Chan is Up and ready!")

    try:
        await bot.tree.sync(guild=discord.Object(id=Config.GUILD_ID))
        logger.debug("Commands synced successfully!")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")

async def load_cogs():
    for filename in os.listdir('./app/cogs'):
        if filename.endswith('.py') and filename != '__init__.py':
            await bot.load_extension(f'app.cogs.{filename[:-3]}')

async def main():
    async with bot:
        await load_cogs()
        await bot.start(Config.DISCORD_TOKEN)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
