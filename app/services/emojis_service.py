import json
import random
import re
import sqlite3
from typing import Dict, Any, Optional, Tuple
import time
from datetime import datetime, timedelta, timezone

import requests
from app.services.database_service import DatabaseService
from app.config import Config
from app.utils.logger import logger
from app.utils.ai_related.groq_api import send_to_groq
from app.utils.ai_related.chatgpt_api import send_to_openai
from app.utils.helpers import get_bot_name_for_guild

class EmojiService:
    def __init__(self):
        self.database = DatabaseService()
        self.config = Config
        self.active_games: Dict[int, Dict[str, Any]] = {}
        self.cooldown_hours = self.config.COOLDOWN_HOURS  # Use the global cooldown_minutes
        self.max_stacked_usages = 4
        self.initial_usages = 2  # Initial usages for new users
        self.emoji_key = self.config.EMOJI_API_KEY

    def generate_emoji_question(self, guild_id: int = None) -> Optional[Dict[str, Any]]:
        emojis = self.fetch_emojis()
        emoji_combination = self.create_emoji_combination(emojis)
        if not emoji_combination:
            logger.error("Failed to generate emoji combination")
            return None
        
        bot_name = get_bot_name_for_guild(guild_id) if guild_id else 'Ai-Chan'
        
        messages = [
            {"role": "system", "content": f"You are {bot_name}, the AI assistant from Honkai Impact and mascot of the Bakakats Discord server. Now you are playing an emoji guessing game."},
            {"role": "user", "content": f"""Generate a question using the following emojis: {emoji_combination}
            The question should represent a movie, game, or something well-known.
            Be creative with this emojis, but make sure it's something that can be guessed. Don't be repetitive, try to be unique and fun.
            Provide your response in the following JSON format:
            {{
                "question": "emoji string here",
                "answer": "correct answer here",
                "hint": "hint here"
            }}
            Ensure that your response contains a valid JSON object."""}
        ]
        response, _, _, _ = send_to_openai(messages)
        logger.info(f"OpenAI API response for question generation: {response}")
        
        json_str = self.extract_json_from_response(response)
        if json_str is None:
            logger.error("Failed to extract JSON from OpenAI API response")
            return None

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from OpenAI API response: {e}")
            return None

    def validate_answer(self, question: str, correct_answer: str, user_answer: str) -> Optional[Dict[str, Any]]:
        messages = [
            {"role": "system", "content": "You are an AI assistant that validates answers for an emoji guessing game."},
            {"role": "user", "content": f"""Question: {question}
            Correct Answer: {correct_answer}
            User Answer: {user_answer}
            Check if the user's answer is correct, allowing for minor misspellings, allowing for some fun and creativity but still needs to be mostly true. 
            Provide your response in the following JSON format:
            {{
                "correct": true or false,
                "comment": "Your comment here"
            }}
            Ensure that your response contains a valid JSON object."""}
        ]
        response, _, _, _ = send_to_groq(messages)
        logger.info(f"Groq API response for answer validation: {response}")
        
        json_str = self.extract_json_from_response(response)
        if json_str is None:
            logger.error("Failed to extract JSON from Groq API response")
            return None

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Groq API response: {e}")
            return None

    def extract_json_from_response(self, response: str) -> Optional[str]:
        match = re.search(r'\{[^}]*\}', response)
        return match.group(0) if match else None

    def update_all_usages(self):
        with sqlite3.connect(self.database.path) as conn:
            cursor = conn.cursor()
            logger.debug("Fetching users for usage update.")
            cursor.execute("SELECT user_id, available_usages FROM emoji_game_usage")
            rows = cursor.fetchall()

            logger.debug(f"Found {len(rows)} users to update.")
            for row in rows:
                user_id, available_usages = row
                logger.debug(f"Updating usages for user {user_id}.")
                new_usages = min(self.max_stacked_usages, available_usages + 1)
                cursor.execute("""
                    UPDATE emoji_game_usage
                    SET available_usages = ?
                    WHERE user_id = ?
                """, (new_usages, user_id))
                logger.debug(f"Updated usages for user {user_id} to {new_usages}.")

            conn.commit()
            logger.debug("All users' usages updated.")


    def update_user_usage(self, user_id: int):
        """Update a single user's usage count, adding new users with initial usages if necessary."""
        with sqlite3.connect(self.database.path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT available_usages FROM emoji_game_usage
                WHERE user_id = ?
            """, (user_id,))
            result = cursor.fetchone()

            if result:
                new_usages = min(self.max_stacked_usages, result[0] - 1)
                cursor.execute("""
                    UPDATE emoji_game_usage
                    SET available_usages = ?
                    WHERE user_id = ?
                """, (new_usages, user_id))
            else:
                # Assuming first time user if no record found.
                cursor.execute("""
                    INSERT INTO emoji_game_usage (user_id, available_usages)
                    VALUES (?, ?)
                """, (user_id, self.initial_usages))

            conn.commit()

    def calculate_global_usages(self, last_updated: Optional[int], available_usages: int, current_time: int) -> int:
        if last_updated is None:
            # If last_updated is None, assume it's the first update and give initial usages
            last_updated = current_time - (self.cooldown_hours * 3600)
        time_passed = current_time - last_updated
        periods_passed = time_passed // (self.cooldown_hours * 3600)
        new_usages = min(self.max_stacked_usages, available_usages + periods_passed)
        return new_usages

    def get_next_global_refresh_time(self) -> datetime:
        current_time = datetime.now(timezone.utc)
        periods_passed = current_time.hour // self.cooldown_hours
        last_refresh_time = current_time.replace(hour=periods_passed * self.cooldown_hours, minute=0, second=0, microsecond=0)
        next_refresh_time = last_refresh_time + timedelta(hours=self.cooldown_hours)
        return next_refresh_time


    def get_user_usage(self, user_id: int) -> Optional[int]:
        """Fetch the user's available usages from the database."""
        with sqlite3.connect(self.database.path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT available_usages FROM emoji_game_usage
                WHERE user_id = ?
            """, (user_id,))
            result = cursor.fetchone()
        print(f"get_user_usage for user_id {user_id}: {result} (type: {type(result)})")
        return result[0] if result else None


    

    def can_play(self, user_id: int) -> bool:
        """Check if the user can play, updating their usages if they can."""
        usage = self.get_user_usage(user_id)
        print(f"can_play usage for user_id {user_id}: {usage} (type: {type(usage)})")
        if usage is None:
            # First time user or no existing usage info
            self.update_user_usage(user_id)
            return True

        available_usages = usage
        if available_usages > 0:
            self.update_user_usage(user_id)
            return True
        return False



    def get_remaining_usages(self, user_id: int) -> Tuple[int, bool]:
        """Fetch the user's available usages and whether they are in the database."""
        with sqlite3.connect(self.database.path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT available_usages FROM emoji_game_usage
                WHERE user_id = ?
            """, (user_id,))
            result = cursor.fetchone()
        print(f"get_remaining_usages for user_id {user_id}: {result} (type: {type(result)})")
        if result:
            return result[0], False  # Return the usage count and a flag indicating the user is in the database
        else:
            return 0, True  # Return 0 usages and a flag indicating the user is not in the database


    def start_game(self, user_id: int) -> Optional[Dict[str, Any]]:
        print("in start game")
        if not self.can_play(user_id):
            return None

        question_data = self.generate_emoji_question()
        print(f"Generated question data: {question_data} (type: {type(question_data)})")
        if question_data is None:
            return None

        # Add checks to ensure question_data is a dictionary with the expected keys
        if isinstance(question_data, dict) and "question" in question_data and "answer" in question_data:
            self.active_games[user_id] = {
                "question": question_data["question"],
                "answer": question_data["answer"],
            }
            print("after start game")
            return question_data
        else:
            print("Error: question_data is not in the expected format:", question_data)
            return None



    def answer_game(self, user_id: int, user_answer: str):
        if user_id not in self.active_games:
            return None

        game_data = self.active_games[user_id]
        validation_data = self.validate_answer(
            game_data['question'],
            game_data['answer'],
            user_answer
        )

        del self.active_games[user_id]
        return validation_data

    def fetch_emojis(self):
        url = f"https://emoji-api.com/emojis?access_key={self.emoji_key}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return []

    def create_emoji_combination(self, emojis, min_emojis=2, max_emojis=5):
        valid_emojis = [emoji for emoji in emojis if 'character' in emoji and emoji['character'].isprintable()]
        num_emojis = random.randint(min_emojis, max_emojis)
        if len(valid_emojis) >= num_emojis:
            emoji_combination = random.sample(valid_emojis, num_emojis)
            question_emojis = ''.join([emoji['character'] for emoji in emoji_combination])
            return question_emojis
        return ''