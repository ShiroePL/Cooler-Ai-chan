import os
import random
import re
import hashlib


from decimal import Decimal
import sqlite3


def hash_username(username):
    # Remove any characters that are not alphanumeric (letters and numbers)
    username = username.lower()
    sanitized_username = re.sub(r'[^a-zA-Z0-9]', '', username)
    # Compute the SHA-1 hash of the original username
    hashed_username = hashlib.sha1(username.encode()).hexdigest()
    # Combine the sanitized username and the hash
    combined_username = f"{sanitized_username}{hashed_username}"
    return combined_username


# sql for creating table
# CREATE TABLE IF NOT EXISTS tic_tac_toe_games (
#     game_id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
#     discord_username VARCHAR(255) NOT NULL,
#     bot_last_response TEXT, 
#     board_state CHAR(9) NOT NULL DEFAULT '.........',
#     game_status ENUM('ongoing', 'win', 'tie') NOT NULL DEFAULT 'ongoing',
#     difficulty VARCHAR(10) NOT NULL DEFAULT ,
#     last_move_player VARCHAR(20) NOT NULL DEFAULT , player or bot
#     player_mark CHAR(1) NOT NULL DEFAULT ,
# );
current_working_directory = os.getcwd()
# Construct the path relative to the current working directory
data_directory = os.path.join(current_working_directory, "app", "persistent_data", "database")

if not os.path.exists(data_directory):
    os.makedirs(data_directory)
path = os.path.join(data_directory, "database.db")

def get_game_variables(interaction, difficulty, last_move_player=None):
    discord_username = hash_username(interaction.user.name)
    try:
        with sqlite3.connect(path) as conn:
            cursor = conn.cursor()

            # Query to check if user_id exists in the 'games' table and retrieve its game_status
            query = """
                SELECT game_id, bot_last_response, game_status, board_state, difficulty, last_move_player, player_mark 
                FROM tic_tac_toe_games 
                WHERE discord_username = ?
            """
            cursor.execute(query, (discord_username,))
            result = cursor.fetchone()

            if result:
                game_id, bot_last_response, game_status, board_state, difficulty, last_move_player, player_mark = result
                return {
                    "game_id": game_id,
                    "bot_last_response": bot_last_response,
                    "game_status": game_status,
                    "board_state": board_state,
                    "difficulty": difficulty,
                    "last_move_player": last_move_player,
                    "player_mark": player_mark
                }
            else:
                # Setting up a new game for the user with a fresh board
                board_state = '.........'
                game_status = 'ongoing'
                player_mark = "X"  # X because X will be first, and we already randomed who goes first in 'last_move_player'
                bot_last_response = "Let's start the game!"

                # You might need to adjust the insertion if you're using additional fields in the table
                query = """
                    INSERT INTO tic_tac_toe_games (discord_username, board_state, game_status, difficulty, last_move_player, player_mark, bot_last_response) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(query, (discord_username, board_state, game_status, difficulty, last_move_player, player_mark, bot_last_response))
                conn.commit()
                game_id = cursor.lastrowid

                return {
                    "game_id": game_id,
                    "game_status": game_status,
                    "board_state": board_state,
                    "difficulty": difficulty,
                    "last_move_player": last_move_player,
                    "player_mark": player_mark,
                    "bot_last_response": bot_last_response
                }
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return None

def send_new_game_variables(interaction, board_state, bot_last_response, last_move_player, player_mark, move_history):
    discord_username = hash_username(interaction.user.name)
    try:
        with sqlite3.connect(path) as conn:
            cursor = conn.cursor()

            query = """
                UPDATE tic_tac_toe_games 
                SET board_state = ?, bot_last_response = ?, last_move_player = ?, player_mark = ?, move_history = ?
                WHERE discord_username = ?
            """
            cursor.execute(query, (board_state, bot_last_response, last_move_player, player_mark, move_history, discord_username))
            conn.commit()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

def finish_game_aka_delete_user_from_table(interaction, game_id):
    discord_username = hash_username(interaction.user.name)
    try:
        with sqlite3.connect(path) as conn:
            cursor = conn.cursor()

            query = """
                DELETE FROM tic_tac_toe_games 
                WHERE discord_username = ? AND game_id = ?
            """
            cursor.execute(query, (discord_username, game_id))
            conn.commit()
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    

def add_tokens_to_db():
    pass