import discord
from discord.ext import commands
from app.config import Config
from app.utils.logger import logger
from app.cogs.command_handling_service_cog import CommandHandlingService
from app.utils.command_utils import custom_command
class General(commands.Cog):
    def __init__(self, bot):
        try:
            self.bot = bot
            self.command_handling_service = CommandHandlingService(bot)
            self.config = Config()
        except Exception as e:
            logger.error(f"Error initializing General cog: {e}")
            raise

    @custom_command(name='sync')
    async def sync_commands(self, ctx):
        if ctx.author.id == self.config.master_user_id: # currently its AI shiro id
            try:
                # Attempt to sync the commands and log each one
                synced_commands = await self.bot.tree.sync()
                logger.info("Commands synced successfully!")
                logger.info(f"Synced commands: {', '.join([command.name for command in synced_commands])}")
                await ctx.send(f"Commands synced successfully! Synced commands: {', '.join([command.name for command in synced_commands])}")
            except discord.errors.Forbidden as e:
                logger.error(f"Failed to sync commands due to permission error: {e}")
                await ctx.send(f"Failed to sync commands due to permission error: {e}")
                # Log detailed info about permissions
                for guild in self.bot.guilds:
                    logger.info(f"Checking permissions for guild: {guild.name} ({guild.id})")
                    bot_member = guild.get_member(self.bot.user.id)
                    if bot_member is not None:
                        permissions = bot_member.guild_permissions
                        logger.info(f"Bot permissions in {guild.name}: {permissions}")
                        if not permissions.administrator:
                            logger.warning(f"Bot does not have administrator permissions in {guild.name}")
                    else:
                        logger.warning(f"Bot is not a member of the guild {guild.name}")
            except discord.errors.HTTPException as e:
                logger.error(f"Failed to sync commands due to HTTP error: {e}")
                await ctx.send(f"Failed to sync commands due to HTTP error: {e}")
            except Exception as e:
                logger.error(f"Failed to sync commands: {e}")
                await ctx.send(f"Failed to sync commands: {e}")
        else:
            await ctx.send("You do not have permission to use this command.")

    @commands.command(name='shutdown', hidden=True)
    async def shutdown(self, ctx):
        if ctx.author.id != self.config.master_user_id:
            await ctx.send("You do not have permission to shut down the bot.")
            return
        
        await ctx.send("Shutting down...")
        await self.bot.close()
        logger.info("Bot shut down gracefully, state saved.")

async def setup(bot):
    try:
        await bot.add_cog(General(bot))
        logger.info("General cog loaded successfully")
    except Exception as e:
        logger.error(f"Error setting up General cog: {e}")
        raise
