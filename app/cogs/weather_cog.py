import os
import time
import discord
from discord.ext import commands, tasks
from app.utils.logger import logger
from app.services.weather_service import WeatherService

class WeatherCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.weather_service = WeatherService()
        self.map_cache = {}
        self.map_cleaner.start()

    def cog_unload(self):
        self.map_cleaner.cancel()

    @tasks.loop(minutes=1)
    async def map_cleaner(self):
        #logger.info("Running map cache cleaner")
        current_time = time.time()
        for key, (timestamp, _) in list(self.map_cache.items()):
            if current_time - timestamp > 600:  # 10 minutes
                file_path = self.map_cache[key][1]
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Removed map cache file: {file_path}")
                del self.map_cache[key]

    @commands.hybrid_command(name='weather', help="Fetches and displays weather information for a specified city.")
    async def weather(self, ctx, *, city: str):
        """Fetches and displays weather information for a specified city (text only)."""
        try:
            weather_data = await self.weather_service.get_weather_data(city)
            if weather_data:
                embed = self.create_weather_embed(city, weather_data)
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"Could not fetch weather data for {city}. Please try again.")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            await ctx.send("An unexpected error occurred. Please try again later.")

    @commands.hybrid_command(name='weathermap', help="Fetches weather information and map for a specified city with optional map size.")
    async def weather_map(self, ctx, *, args):
        """Fetches weather information and map for a specified city with optional map size."""
        try:
            parts = args.rsplit(' ', 1)
            if len(parts) == 2 and parts[1].lower() in ['small', 'medium', 'big']:
                city = parts[0]
                map_size = parts[1].lower()
            else:
                city = args
                map_size = 'medium'  # Default size

            weather_data = await self.weather_service.get_weather_data(city)
            if weather_data:
                embed = self.create_weather_embed(city, weather_data)
                
                zoom = self.get_zoom_level(map_size)
                map_path = await self.get_or_create_map(city, weather_data['lat'], weather_data['lon'], zoom)
                
                if map_path:
                    file = discord.File(map_path, filename="weather_map.png")
                    embed.set_image(url="attachment://weather_map.png")
                    await ctx.send(embed=embed, file=file)
                else:
                    await ctx.send(embed=embed)
                    await ctx.send("Failed to generate the weather map. Showing text data only.")
            else:
                await ctx.send(f"Could not fetch weather data for {city}. Please try again.")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            await ctx.send("An unexpected error occurred. Please try again later.")

    @commands.hybrid_command(name='weatherhelp', help="Displays help information for weather-related commands.")
    async def weatherhelp(self, ctx):
        """Displays help information for weather-related commands."""
        embed = discord.Embed(
            title="Weather Commands Help",
            description="Here's how to use the weather commands:",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="+weather <city>",
            value="Fetches and displays weather information for a specified city (text only).\n"
                  "Example: `+weather New York`",
            inline=False
        )

        embed.add_field(
            name="+weathermap <city> [size]",
            value="Fetches weather information and map for a specified city.\n"
                  "Optional: Add **'small', 'medium', or 'big'** at the end to specify map size.\n"
                  "Examples:\n"
                  "`+weathermap London` **(default medium size)**\n"
                  "`+weathermap Paris big`",
            inline=False
        )

        embed.add_field(
            name="Map Sizes",
            value="**small:** zoomed out view\n"
                  "**medium:** balanced view (default)\n"
                  "**big:** zoomed in view",
            inline=False
        )

        embed.set_footer(text="For more help, ask ._.shiro._.")

        await ctx.send(embed=embed)

    def create_weather_embed(self, city, weather_data):
        embed = discord.Embed(
            title=f"Weather in {city}",
            description=f"{weather_data['description'].capitalize()}",
            color=discord.Color.blue()
        )
        
        # Current weather
        current = f"🌡️ {weather_data['temperature']:.1f}°C (Feels like {weather_data['feels_like']:.1f}°C)\n"
        current += f"💨 {weather_data['wind_speed']:.1f} km/h {self.get_wind_direction_arrow(weather_data['wind_direction'])}\n"
        current += f"💧 {weather_data['humidity']}%\n"
        current += f"👁️ {weather_data['visibility'] / 1000:.1f} km"
        embed.add_field(name="Current", value=current, inline=False)
        
        # Forecast
        if 'forecast' in weather_data:
            forecast = weather_data['forecast'][:8]  # Next 24 hours in 3-hour intervals
            forecast_text = ""
            for time, temp, desc, rain_prob in forecast:
                forecast_text += f"**{time[11:16]}** {temp:.1f}°C, {desc.capitalize()}, ☔ {rain_prob:.0f}%\n"
            embed.add_field(name="Forecast (Next 24 hours)", value=forecast_text, inline=False)
        
        embed.set_thumbnail(url=weather_data['icon_url'])
        embed.set_footer(text="Weather data provided by OpenWeatherMap")
        return embed

    def get_wind_direction_arrow(self, degrees):
        arrows = ["⬆️", "↗️", "➡️", "↘️", "⬇️", "↙️", "⬅️", "↖️"]
        index = round(degrees / 45) % 8
        return arrows[index]

    @staticmethod
    def get_zoom_level(map_size):
        return {'small': 4, 'medium': 5, 'big': 7}[map_size]

    async def get_or_create_map(self, city, lat, lon, zoom):
        cache_key = f"{city}_{zoom}"
        current_time = time.time()

        if cache_key in self.map_cache:
            self.map_cache[cache_key] = (current_time, self.map_cache[cache_key][1])
            return self.map_cache[cache_key][1]

        map_path = f'app/services/weather_data/{cache_key}.png'
        weather_map = await self.weather_service.create_centered_weather_map(lat, lon, zoom, city)
        
        if weather_map:
            os.makedirs('app/services/weather_data', exist_ok=True)
            with open(map_path, 'wb') as f:
                f.write(weather_map.getvalue())
            self.map_cache[cache_key] = (current_time, map_path)
            return map_path
        return None

async def setup(bot: commands.Bot):
    await bot.add_cog(WeatherCog(bot))