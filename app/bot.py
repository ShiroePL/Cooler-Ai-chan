from datetime import datetime, timedelta
import discord
from discord.ext import commands, tasks
from app.config import Config
import os
from app.utils.logger import logger
from app.services.database_service import DatabaseService
from app.discord_games.tic_tac_toe.tic_tac_toe import start_tic_tac_toc
from app.services.emojis_service import EmojiService
import asyncio
import json

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.messages = True
intents.guilds = True
intents.presences = True  # Enable the presences intent

database = DatabaseService()
bot = commands.Bot(command_prefix=Config.PREFIX, intents=intents)
emoji_service = EmojiService()

@bot.event
async def on_ready():
    logger.info("------")
    logger.info("Cooler AI-Chan is Up and ready!")
    bot.bot_id = bot.user.id  # Set bot's user ID
    logger.info(f"Bot ID is {bot.bot_id}")
    #logger.debug(f"Bot environment is set to {Config.ENVIRONMENT}")

    # Check missed alarms
    logger.info("Checking missed alarms")
    alarm_cog = bot.get_cog("AlarmCog")
    if alarm_cog:
        logger.info("Found AlarmCog, checking existing alarms")
        await alarm_cog.check_existing_alarms()
        logger.info("Checked missed alarms")
    else:
        logger.error("AlarmCog not found")


    # Start the initial delay task
    bot.loop.create_task(test_initial_delay_and_start_task())

    # Sync the slash commands
    try:
        await bot.tree.sync(guild=discord.Object(id=Config.GUILD_ID))
        logger.debug("Commands synced successfully!")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")

######################################################################################

async def test_calculate_initial_delay():
    now = datetime.now()
    print(f"Current time: {now}")

    # Start from today at the reference hour
    reference_time = now.replace(hour=Config.REFERENCE_HOUR, minute=0, second=0, microsecond=0)
    print(f"Base reference time: {reference_time}")
    
    # Calculate all trigger times for the next 24 hours
    trigger_times = []
    hours_in_day = 24
    for i in range(hours_in_day // Config.COOLDOWN_HOURS):
        trigger_time = reference_time + timedelta(hours=i * Config.COOLDOWN_HOURS)
        if trigger_time <= now:
            trigger_time += timedelta(days=1)
        trigger_times.append(trigger_time)
    
    print("Next few trigger times:")
    for t in trigger_times[:5]:  # Print only the next 5 for brevity
        print(f"  {t}")
    
    # Find the next trigger time
    next_trigger_time = min(trigger_times)
    print(f"Next trigger time: {next_trigger_time}")
    
    # Calculate the delay
    initial_delay = (next_trigger_time - now).total_seconds()
    return initial_delay

async def test_initial_delay_and_start_task():
    initial_delay = await test_calculate_initial_delay()
    print(f"Initial delay calculated: {initial_delay:.2f} seconds")
    print(f"This is approximately {initial_delay / 3600:.2f} hours")
    
    # Wait for the initial delay
    await asyncio.sleep(initial_delay)
    print("Initial delay complete, starting recurring task")





######################################################################################

@tasks.loop(hours=Config.COOLDOWN_HOURS)  # Use the global cooldown interval
async def update_usages():
    logger.warning("Updating emoji game usages for all users.")
    try:
        emoji_service.update_all_usages()
        logger.warning("Usages updated successfully.")
    except Exception as e:
        logger.error(f"Failed to update usages: {e}")


@bot.event
async def on_command(ctx):
    user = ctx.author
    command = ctx.command
    channel = ctx.channel
    bot_id = bot.bot_id
    params = {param: value for param, value in ctx.kwargs.items()}
    params.update({param: value for param, value in zip(command.clean_params, ctx.args[2:])})
    logger.warning(f"Command '{command}' used by '{user}' in channel '{channel}' with params: {params}")
    level_up, _ = database.add_exp(bot_id, 1)

    if level_up:
        await ctx.send(f"🎉 Level Up! 🎉 Congratulations to MYSELF! Aichan just leveled up! GRIND GRIND GRIND")
        logger.info(f"Bot leveled up!")



@bot.tree.command(name="tic_tac_toe")
async def tic_tac_toe(interaction: discord.Interaction, difficulty: str):
    await start_tic_tac_toc(interaction, difficulty)

async def load_cogs():
    cogs_loaded = []
    for root, dirs, files in os.walk('./app'):
        for filename in files:
            if filename.endswith('_cog.py') or filename == 'help_cog.py':
                relative_path = os.path.relpath(root, './app').replace(os.path.sep, '.')
                module_name = f'app.{relative_path}.{filename[:-3]}' if relative_path != '.' else f'app.{filename[:-3]}'
                try:
                    await bot.load_extension(module_name)
                    cogs_loaded.append(module_name)
                except Exception as e:
                    logger.error(f"Failed to load cog {module_name}: {e}")
    logger.info("Loaded cogs: " + ", ".join(cogs_loaded))

def verify_json_files():
    log_directory = "app/persistent_data/logs/message_logs"
    if os.path.exists(log_directory):
        for filename in os.listdir(log_directory):
            if filename.endswith('.json'):
                file_path = os.path.join(log_directory, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        json.load(f)
                except json.JSONDecodeError as e:
                    logger.error(f"Corrupted JSON file found: {file_path}")
                    # Backup the corrupted file
                    backup_path = f"{file_path}.corrupted"
                    os.rename(file_path, backup_path)
                    # Create new empty JSON file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump([], f)

async def main():
    verify_json_files()  # Add this line before loading cogs
    async with bot:
        await load_cogs()
        await bot.start(Config.DISCORD_TOKEN)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
