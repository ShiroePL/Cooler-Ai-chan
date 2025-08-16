import sqlite3
import os
import random
from app.utils.logger import logger

class DatabaseService:
    def __init__(self):
        # Get the current working directory where the app is run
        current_working_directory = os.getcwd()
        # Construct the path relative to the current working directory
        data_directory = os.path.join(current_working_directory, "app", "persistent_data", "database")

        if not os.path.exists(data_directory):
            os.makedirs(data_directory)

        self.path = os.path.join(data_directory, "database.db")
        self._initialize_database()

    def _initialize_database(self):
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                nicknames TEXT,
                points INTEGER DEFAULT 0,
                exp INTEGER DEFAULT 0,
                total_exp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1
            )""")
            
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS nicknames (
                user_id INTEGER,
                nickname TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )""")

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS pictures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT,
                link TEXT
            )""")

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS tic_tac_toe_games (
                game_id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_username TEXT NOT NULL,
                bot_last_response TEXT DEFAULT 'lets start!',
                board_state CHAR(9) NOT NULL DEFAULT '         ',
                game_status TEXT NOT NULL DEFAULT 'ongoing',
                difficulty TEXT NOT NULL,
                last_move_player TEXT NOT NULL,
                player_mark CHAR(1) NOT NULL,
                move_history TEXT NOT NULL DEFAULT 'New game begins'
            )
        """)
            
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS alarms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                channel_id INTEGER,
                trigger_time INTEGER,
                note TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )""")

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS emoji_game_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                available_usages INTEGER,
                last_updated INTEGER,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )""")
            
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS guild_bot_names (
                guild_id INTEGER PRIMARY KEY,
                bot_name TEXT NOT NULL DEFAULT 'Ai-Chan'
            )""")

        conn.commit()
            

    def insert_nicknames(self, user_id, nicknames):
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            for nickname in nicknames:
                cursor.execute("INSERT INTO nicknames (user_id, nickname) VALUES (?, ?)", (user_id, nickname))
            conn.commit()
            
    def add_user(self, user):
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            
            # Check if user already exists
            cursor.execute("SELECT 1 FROM users WHERE id = ?", (user.id,))
            user_exists = cursor.fetchone()
            
            if not user_exists:
                # User does not exist, insert them
                cursor.execute("""
                INSERT OR IGNORE INTO users (id, name, nicknames, points, exp, total_exp, level)
                VALUES (?, ?, ?, 0, 0, 0, 1)""", (user.id, user.name, user.name))
                conn.commit()
                logger.info(f"User added: {user.name} (ID: {user.id})")

    def add_point(self, user_id: int):
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET points = points + 1 WHERE id = ?", (user_id,))
            conn.commit()

    def subtract_point(self, user_id: int):
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET points = points - 1 WHERE id = ?", (user_id,))
            conn.commit()

    def get_points(self, user_id: int) -> int:
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT points FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else 0

    def add_nickname(self, user_id: int, nickname: str):
        if not nickname:
            return

        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            # Check if the nickname already exists for this user
            cursor.execute("SELECT nickname FROM nicknames WHERE user_id = ? AND nickname = ?", (user_id, nickname))
            result = cursor.fetchone()
            if not result:
                # Insert the new nickname
                cursor.execute("INSERT INTO nicknames (user_id, nickname) VALUES (?, ?)", (user_id, nickname))
                conn.commit()

    def get_nicknames(self, user_id: int) -> list:
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT nickname FROM nicknames WHERE user_id = ?", (user_id,))
            results = cursor.fetchall()
            return [row[0] for row in results]

    def get_exp(self, user_id: int) -> int:
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT exp FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else 0

    def get_total_exp(self, user_id: int) -> int:
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT total_exp FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else 0

    def add_exp(self, user_id: int, amount: int) -> tuple:
        level_up = False
        level_down = False
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT exp, level, total_exp FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            user_name = cursor.execute("SELECT name FROM users WHERE id = ?", (user_id,)).fetchone()[0]
            if result:
                exp, level, total_exp = result
                #print(f"Initial values - exp: {exp}, level: {level}, total_exp: {total_exp}")

                total_exp += amount
                if total_exp < 0:
                    total_exp = 0
                
                # Calculate new level based on total experience
                new_level = self.calculate_level(total_exp)
                exp_in_level = total_exp - self.experience_to_reach_level(new_level)
                
                if new_level > level:
                    level_up = True
                elif new_level < level:
                    level_down = True
                
                cursor.execute("UPDATE users SET exp = ?, total_exp = ?, level = ? WHERE id = ?", (exp_in_level, total_exp, new_level, user_id))
                conn.commit()
                logger.debug(f"user {user_name} GOT 1 EXP total_exp: {total_exp}")
            else:
                print(f"User {user_name} not found.")
        return level_up, level_down

    def experience_to_reach_level(self, level: int) -> int:
        """Calculates the total experience required to reach the given level."""
        return sum((i * 100) for i in range(1, level))

    def calculate_level(self, total_exp: int) -> int:
        """Calculates the level based on total experience."""
        level = 1
        while total_exp >= self.experience_to_reach_level(level + 1):
            level += 1
        return level



    def get_level_info(self, user_id: int) -> tuple:
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT level, total_exp FROM users WHERE id = ?", (user_id,))
            result = cursor.fetchone()
            if result:
                level, total_exp = result
                exp_in_level = total_exp - self.experience_to_reach_level(level)
                return level, f"{exp_in_level}/{level * 100}", total_exp
            return 0, "0/0", 0



    def get_leaderboard(self) -> str:
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, level, exp FROM users ORDER BY level DESC, exp DESC LIMIT 10")
            results = cursor.fetchall()
            leaderboard = "\n".join([f"{i + 1}. {name} | Lv. {level} | Exp. {exp}" for i, (name, level, exp) in enumerate(results)])
            return leaderboard

    def add_picture(self, type: str, link: str):
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO pictures (type, link) VALUES (?, ?)", (type, link))
            conn.commit()

    def get_random_picture(self, type: str) -> str:
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT link FROM pictures WHERE type = ?", (type,))
            results = cursor.fetchall()
            if results:
                return random.choice(results)[0]
            return None

    def get_pictures(self, type: str) -> list:
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT link FROM pictures WHERE type = ?", (type,))
            results = cursor.fetchall()
            return [result[0] for result in results]

    def list_users(self):
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, level, exp, total_exp FROM users")
            results = cursor.fetchall()
            for user in results:
                logger.debug(user)

    def insert_alarm(self, user_id, channel_id, trigger_time, note):
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO alarms (user_id, channel_id, trigger_time, note)
            VALUES (?, ?, ?, ?)""", (user_id, channel_id, trigger_time, note))
            conn.commit()
            return cursor.lastrowid  # Return the ID of the newly inserted alarm

    def delete_alarm(self, alarm_id):
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM alarms WHERE id = ?", (alarm_id,))
            conn.commit()

    def get_alarms(self):
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, user_id, channel_id, trigger_time, note FROM alarms")
            return cursor.fetchall()

    def get_user_alarms(self, user_id):
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, trigger_time, note FROM alarms WHERE user_id = ?", (user_id,))
            return cursor.fetchall()
    
    def delete_user_alarms(self, user_id):
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM alarms WHERE user_id = ?", (user_id,))
            conn.commit()
    
    def set_guild_bot_name(self, guild_id: int, bot_name: str):
        """Set the bot name for a specific guild."""
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO guild_bot_names (guild_id, bot_name) 
                VALUES (?, ?)
            """, (guild_id, bot_name))
            conn.commit()
            logger.info(f"Bot name set to '{bot_name}' for guild {guild_id}")
    
    def get_guild_bot_name(self, guild_id: int) -> str:
        """Get the bot name for a specific guild, returns 'Ai-Chan' as default."""
        with sqlite3.connect(self.path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT bot_name FROM guild_bot_names WHERE guild_id = ?", (guild_id,))
            result = cursor.fetchone()
            return result[0] if result else 'Ai-Chan'