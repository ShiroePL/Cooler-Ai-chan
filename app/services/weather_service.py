import math
import requests
from io import BytesIO
from PIL import Image, ImageDraw
from app.config import Config
from app.utils.logger import logger

class WeatherService:
    def __init__(self):
        self.openweather_api_key = Config.OPENWEATHER_API_KEY
        self.tomorrow_api_key = Config.TOMORROW_API_KEY
        self.user_agent = {"User-Agent": "DiscordWeatherBot/1.0"}

    async def create_centered_weather_map(self, lat, lon, zoom, city):
        """Creates a centered weather map for given coordinates and zoom level."""
        try:
            # Calculate tile coordinates
            tile_x, tile_y = self.lat_lon_to_tile(lat, lon, zoom)
            
            # Calculate pixel coordinates within the tile
            pixel_x, pixel_y = self.lat_lon_to_pixel(lat, lon, zoom)
            
            # Determine which tiles to fetch
            tiles_to_fetch = self.get_tiles_to_fetch(tile_x, tile_y, pixel_x, pixel_y)
            
            # Fetch and combine tiles
            combined_image = await self.fetch_and_combine_tiles(tiles_to_fetch, zoom)
            
            if combined_image:
                # Add weather layers
                weather_layers = await self.fetch_weather_layers(tiles_to_fetch, zoom)
                for layer in weather_layers:
                    combined_image = Image.alpha_composite(combined_image, layer)
                
                # Mark the city location
                draw = ImageDraw.Draw(combined_image)
                city_x = pixel_x + 256 * (1 if pixel_x < 128 else 0)
                city_y = pixel_y + 256 * (1 if pixel_y < 128 else 0)
                draw.ellipse([city_x-5, city_y-5, city_x+5, city_y+5], fill='red', outline='white')
                
                # Save the combined image
                combined_image_bytes = BytesIO()
                combined_image.save(combined_image_bytes, format='PNG')
                combined_image_bytes.seek(0)
                
                return combined_image_bytes
            else:
                logger.error("Failed to create combined image")
        except Exception as e:
            logger.error(f"An error occurred while creating centered weather map: {e}")
        return None

    @staticmethod
    def lat_lon_to_tile(lat, lon, zoom):
        lat_rad = math.radians(lat)
        n = 2.0 ** zoom
        x_tile = int((lon + 180.0) / 360.0 * n)
        y_tile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
        return x_tile, y_tile

    @staticmethod
    def lat_lon_to_pixel(lat, lon, zoom):
        lat_rad = math.radians(lat)
        n = 2.0 ** zoom
        x_pixel = int(((lon + 180.0) / 360.0 * n - int((lon + 180.0) / 360.0 * n)) * 256)
        y_pixel = int(((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n
                       - int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)) * 256)
        return x_pixel, y_pixel

    @staticmethod
    def get_tiles_to_fetch(tile_x, tile_y, pixel_x, pixel_y):
        """Determine which 2x2 grid of tiles to fetch based on city location within its tile."""
        if pixel_x < 128:
            if pixel_y < 128:
                return [
                    (tile_x - 1, tile_y - 1), (tile_x, tile_y - 1),
                    (tile_x - 1, tile_y), (tile_x, tile_y)
                ]
            else:
                return [
                    (tile_x - 1, tile_y), (tile_x, tile_y),
                    (tile_x - 1, tile_y + 1), (tile_x, tile_y + 1)
                ]
        else:
            if pixel_y < 128:
                return [
                    (tile_x, tile_y - 1), (tile_x + 1, tile_y - 1),
                    (tile_x, tile_y), (tile_x + 1, tile_y)
                ]
            else:
                return [
                    (tile_x, tile_y), (tile_x + 1, tile_y),
                    (tile_x, tile_y + 1), (tile_x + 1, tile_y + 1)
                ]


    async def fetch_and_combine_tiles(self, tiles, zoom):
        combined_image = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
        for i, (x, y) in enumerate(tiles):
            satellite_url = f"https://tile.openstreetmap.org/{zoom}/{x}/{y}.png"
            response = requests.get(satellite_url, headers=self.user_agent)
            if response.status_code == 200:
                tile_image = Image.open(BytesIO(response.content)).convert("RGBA")
                combined_image.paste(tile_image, (256 * (i % 2), 256 * (i // 2)))
            else:
                logger.error(f"Failed to fetch tile at {x},{y}. Status code: {response.status_code}")
                return None
        return combined_image
    
    

    async def fetch_weather_layers(self, tiles, zoom):
        combined_layer = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
        
        
        for i, (x, y) in enumerate(tiles):
            temp_url = f"https://api.tomorrow.io/v4/map/tile/{zoom}/{x}/{y}/temperature/now.png?apikey={self.tomorrow_api_key}"
            precip_url = f"https://api.tomorrow.io/v4/map/tile/{zoom}/{x}/{y}/precipitationIntensity/now.png?apikey={self.tomorrow_api_key}"
            
            temp_response = requests.get(temp_url)
            precip_response = requests.get(precip_url)
            
            if temp_response.status_code == 200 and precip_response.status_code == 200:
                temp_image = Image.open(BytesIO(temp_response.content)).convert("RGBA")
                precip_image = Image.open(BytesIO(precip_response.content)).convert("RGBA")
                
                # Adjust opacity
                temp_image = Image.blend(Image.new("RGBA", temp_image.size, (0, 0, 0, 0)), temp_image, 0.6)
                precip_image = Image.blend(Image.new("RGBA", precip_image.size, (0, 0, 0, 0)), precip_image, 0.6)
                
                # Combine temperature and precipitation layers
                tile_layer = Image.alpha_composite(temp_image, precip_image)
                
                # Paste into the correct position in the combined layer
                combined_layer.paste(tile_layer, (256 * (i % 2), 256 * (i // 2)))
            else:
                logger.error(f"Failed to fetch weather layers for tile {x},{y}")
        return [combined_layer]  # Return as a list to maintain compatibility with the existing code
    
    async def get_weather_data(self, city: str):
        weather_url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.openweather_api_key}&units=metric'
        forecast_url = f'http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={self.openweather_api_key}&units=metric'
        
        try:
            weather_response = requests.get(weather_url)
            weather_response.raise_for_status()
            weather_data = weather_response.json()
            
            forecast_response = requests.get(forecast_url)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()
            
            current_weather = {
                'temperature': weather_data['main']['temp'],
                'feels_like': weather_data['main']['feels_like'],
                'humidity': weather_data['main']['humidity'],
                'pressure': weather_data['main']['pressure'],
                'wind_speed': weather_data['wind']['speed'] * 3.6,  # Convert m/s to km/h
                'wind_direction': weather_data['wind']['deg'],
                'visibility': weather_data['visibility'],
                'description': weather_data['weather'][0]['description'],
                'icon_code': weather_data['weather'][0]['icon'],
                'icon_url': f'http://openweathermap.org/img/wn/{weather_data["weather"][0]["icon"]}.png',
                'lat': weather_data['coord']['lat'],
                'lon': weather_data['coord']['lon'],
            }
            
            forecast = []
            for item in forecast_data['list'][:8]:  # Next 24 hours (3-hour intervals)
                forecast.append((
                    item['dt_txt'],
                    item['main']['temp'],
                    item['weather'][0]['description'],
                    item['pop'] * 100  # Probability of precipitation
                ))
            
            current_weather['forecast'] = forecast
            
            return current_weather
        except requests.RequestException as e:
            logger.error(f"Error fetching weather data: {e}")
            return None