import random
import discord 
from app.services.database_service import DatabaseService


def calculate_exp_bonus():
    return 1000 if random.random() < 0.001 else 0

def get_bot_name_for_guild(guild_id: int) -> str:
    """Get the configured bot name for a specific guild."""
    db_service = DatabaseService()
    return db_service.get_guild_bot_name(guild_id)

def get_bot_name_from_context(ctx) -> str:
    """Get bot name from Discord context (command context or interaction)."""
    if hasattr(ctx, 'guild') and ctx.guild:
        return get_bot_name_for_guild(ctx.guild.id)
    return 'Ai-Chan'  # Default fallback

async def extract_user(ctx, specified_user):
    if len(ctx.message.mentions) > 0:
        return ctx.message.mentions[0]
    else:
        return discord.utils.find(lambda m: m.name == specified_user, ctx.guild.members)

async def user_not_found(ctx, user):
    if user is None:
        await ctx.send("User not found.")
        return True
    return False