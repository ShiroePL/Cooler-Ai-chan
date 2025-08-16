import aiohttp
import discord
from app.utils.helpers import get_bot_name_from_context

async def create_embed_with_image(title, url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            image_url = data.get("url")

    embed = discord.Embed(title=title)
    embed.set_image(url=image_url)
    return embed

async def create_slot_machine_embed(ctx, display, messages, exp_message, color, additional_message, multiplier, exp_left, jar_messgage):
    embed = discord.Embed(title="🎰 Slot Machine 🎰", color=color)
    embed.add_field(name="Reels", value=display, inline=False)
    if messages:
        # Join the messages list into a single string with line breaks
        messages_str = ''.join(messages)
        embed.add_field(name="Winning combinations", value=messages_str, inline=False)
    
    embed.add_field(name="Win", value=exp_message, inline=True)
    embed.add_field(name="Multiply", value=f"{multiplier}x", inline=True)
    embed.add_field(name="Exp left", value=exp_left, inline=True)
    if additional_message:
        embed.add_field(name="Final", value=additional_message, inline=False)
    embed.add_field(name="Jar", value=jar_messgage, inline=False)
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
    return embed


async def create_rps101_embed(ctx, user_choice, bot_choice, result_message, bet, color, win_amount, bot_name=None):
    if bot_name is None:
        bot_name = get_bot_name_from_context(ctx)
    embed = discord.Embed(title="RPS101 Game Result", color=color)
    embed.add_field(name="You", value=user_choice, inline=True)
    embed.add_field(name=bot_name, value=bot_choice, inline=True)

    if win_amount > 0 : 
        embed.add_field(name="Won | Bet", value=f"{win_amount} | {bet}", inline=True) 
    else: 
        embed.add_field(name="Bet", value=bet, inline=True)

    embed.add_field(name="Result", value=result_message, inline=False)
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar.url)
    return embed

def get_urban_embed(term, results):
    embed = discord.Embed(
        title=f"Most voted Urban Dictionary definitions for \"{term}\"",
        color=discord.Color.blue()
    )

    for result in results:
        word = result.get('word', 'Unknown')
        definition = result.get('definition', 'No definition')
        example = result.get('example', 'No example')
        author = result.get('author', 'Unknown')
        permalink = result.get('permalink', '')

        # Create the full field value
        field_value = f"{definition}\n\n*Example:* {example}\n*Author:* {author}\n*Link:* [Click here]({permalink})"

        # Truncate the field value if it's too long
        if len(field_value) > 1024:
            field_value = field_value[:1021] + '...'

        embed.add_field(
            name=word,
            value=field_value,
            inline=False
        )

    return embed