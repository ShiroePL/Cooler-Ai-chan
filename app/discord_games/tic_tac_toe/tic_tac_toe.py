import hashlib
import re
import string
import time
from discord.ext import commands
from typing import Optional
import discord
import random
from numpy import diff
from sympy import im, use


from decimal import Decimal
from app.discord_games.tic_tac_toe.database_queries import get_game_variables, send_new_game_variables,finish_game_aka_delete_user_from_table
from app.discord_games.tic_tac_toe.api_requests import get_shiro_response_on_tictactoe
from app.utils.helpers import get_bot_name_from_context

games = {}

class TicTacToe:
    def __init__(self):
        self.board = [['.'] * 3 for _ in range(3)]
        self.player_mark = ''
        self.last_move_player = ''
        self.interaction = None
        self.game_id = None
        self.game_status = None
        self.bot_last_response = None
        self.move_history = ""
        self.who_won = None

    def board_to_string(self):
        return ''.join(cell for row in self.board for cell in row)

    def string_to_board(self, board_str):
        return [list(board_str[i:i+3]) for i in range(0, len(board_str), 3)]

    def make_move(self, position, bot_last_response=None):
        print(f"position: {position}")
        print(f"board: {self.board}")
        row, col = divmod(position, 3)
        print(f"row: {row}, col: {col}")
        if self.board[row][col] == '.':  # . then no one has played there
            self.board[row][col] = self.player_mark  # we set the current player to that position (X or O)

            board_state_str = self.board_to_string()
            print(f"Board State String: {board_state_str}")  # This is the string to be used for database storage

            # Update move history
            move_number = sum(row.count('X') for row in self.board) + sum(row.count('O') for row in self.board)
            self.move_history += f"{move_number}:{position},"  # append the move to the move history
            print(f"move history: {self.move_history}")
            print (f"board before checking game status: {self.board}")


            if self.check_win(self.player_mark):  # Check for win
                self.who_won = f"The  {self.last_move_player }has won!"
                print(f"The  {self.last_move_player }has won!")
                self.set_game_status(f"finished")
                return None
            # Here, check if the opposing player has won
            opposing_mark = 'O' if self.player_mark == 'X' else 'X'

            if self.check_win(opposing_mark):
                self.who_won = f"The player {self.last_move_player }has lost!"
                print(f"The player {self.last_move_player }has lost!")  # or any other actions you'd like to take
                self.set_game_status(f"finished")
                return None
            
            if all(cell != '.' for row in self.board for cell in row):
                print("Tie detected!")
                self.set_game_status("tie")  # Check if all cells are filled to determine tie
                return None

            self.player_mark = 'O' if self.player_mark == 'X' else 'X'
            self.set_last_move_player("player") if self.last_move_player == "bot" else self.set_last_move_player("bot")

            send_new_game_variables(self.interaction, board_state_str, bot_last_response, self.last_move_player, self.player_mark, self.move_history)
            return None


    def check_win(self, mark):
        win_conditions = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6),
                        (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]
        for condition in win_conditions:
            if self.board[condition[0] // 3][condition[0] % 3] == \
            self.board[condition[1] // 3][condition[1] % 3] == \
            self.board[condition[2] // 3][condition[2] % 3] == mark:
                return True
        return False


    def set_board_from_state(self, board_state: str):
        """Sets the game board based on the given board state."""
        self.board = self.string_to_board(board_state)

    def set_game_id(self, game_id: int):
        """Sets the game board based on the given board state."""
        self.game_id = game_id
    
    def set_difficulty(self, difficulty: str):
        """Sets the game difficulty based on the given difficulty."""
        self.difficulty = difficulty
    
    def set_interaction(self, interaction):
        """Sets the game id so we now what game it is."""
        self.interaction = interaction

    def set_player_mark(self, player_mark):
        """Sets the player mark so we know if it is X or O."""
        self.player_mark = player_mark

    def set_last_move_player(self, last_move_player: str):
        """Sets the last move player so we know if the move was made by player or bot."""
        self.last_move_player = last_move_player

    def set_game_status(self, game_status: str):
        """Sets the game status (win, lose, tie, ongoing)."""
        self.game_status = game_status
    def set_bot_last_response(self, bot_last_response: str):
        """Sets the bot's last response message."""
        self.bot_last_response = bot_last_response

    def reset(self):
        self.__init__()

    def minimax(self, board, depth, is_maximizing, player_mark, opponent_mark):
        
        score = self.evaluate(board, player_mark, opponent_mark)

        if score == 10:
            return score - depth

        if score == -10:
            return score + depth

        if not any('.' in sublist for sublist in board):
            return 0

        if is_maximizing:
            best = -1000
            for i in range(3):
                for j in range(3):
                    if board[i][j] == '.':
                        board[i][j] = player_mark    
                        best = max(best, self.minimax(board, depth+1, not is_maximizing, player_mark, opponent_mark))
                        board[i][j] = '.'
            return best
        else:
            best = 1000
            for i in range(3):
                for j in range(3):
                    if board[i][j] == '.':
                        board[i][j] = opponent_mark
                        best = min(best, self.minimax(board, depth+1, not is_maximizing, player_mark, opponent_mark))
                        board[i][j] = '.'
            return best

    def flat_to_2d(self, index):
        row = index // 3
        col = index % 3
        return row, col

    def evaluate(self, board, player_mark, opponent_mark):
        # Updated to use the 2D board directly.
        win_conditions = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]
        for condition in win_conditions:
            if board[condition[0] // 3][condition[0] % 3] == board[condition[1] // 3][condition[1] % 3] == \
                    board[condition[2] // 3][condition[2] % 3]:
                if board[condition[0] // 3][condition[0] % 3] == player_mark:
                    return 10
                elif board[condition[0] // 3][condition[0] % 3] == opponent_mark:
                    return -10
        return 0


    def find_best_moves(self, board, player_mark):
        print(f"board in find_best_move : {board}")
        moves_scores = []

        for i in range(9):  # Looping through all positions
            row, col = divmod(i, 3)
            if board[row][col] == '.':
                board[row][col] = player_mark
                move_val = self.minimax(board, 0, False, player_mark, 'X' if player_mark == 'O' else 'O')
                moves_scores.append((i, move_val))
                board[row][col] = '.'

        # Sort the moves based on their scores
        moves_scores.sort(key=lambda x: x[1], reverse=True)  # Highest scores first

        # Return top 3 moves (or less if not enough moves are available)
        return [move_score[0] for move_score in moves_scores[:3]]


class ButtonGrid(discord.ui.View):

    def __init__(self, board, lock_buttons=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert len(board) == 3 and all(len(row) == 3 for row in board), "Expected a 3x3 board!"
        self.lock_buttons = lock_buttons

        for i in range(3):
            for j in range(3):
                label = board[i][j] if board[i][j] != ' ' else str(i * 3 + j + 1)  # Convert 2D position to flat index for the label
                button = TicTacToeButton(style=discord.ButtonStyle.secondary, label=label, row=i, custom_id=f"button_{i * 3 + j}", disabled=self.lock_buttons)
                button.callback = button_callback  # Don't forget to define your button_callback function
                self.add_item(button)

class TicTacToeButton(discord.ui.Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.label == "O":
            self.style = discord.ButtonStyle.danger  # Red button
            self.label = "O"
        elif self.label == "X":
            self.style = discord.ButtonStyle.primary  # Blue button
            self.label = "X"
        else:  # If it's an empty button or another label
            self.style = discord.ButtonStyle.secondary  # Gray button

      



async def finish_game(interaction, embed, view):
    await interaction.response.edit_message(embed=embed, view=view)


async def button_callback(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id not in games:
        games[user_id] = TicTacToe()

    # Set a local reference to the user's game instance
    game = games[user_id]
    difficulty = game.difficulty
    # Retrieve the current game status from the database
    game_variables = get_game_variables(interaction, difficulty)
    print(f"game status {game_variables}")
    
    # Set the game board based on the retrieved board state
    set_game_state(game, game_variables) # after this  the board is in 2D
    
    position = int(interaction.data["custom_id"].split('_')[-1])
    
    result = game.make_move(position)
    game_status = game.game_status
    if game_status == "finished":
        
        # we need to send to database that game is finished
        finish_game_aka_delete_user_from_table(interaction, game.game_id)
        embed = create_embed(game, game_variables, interaction)
        view = ButtonGrid(game.board)
        await interaction.response.edit_message(embed=embed, view=view)
        await interaction.followup.send(str(game.who_won))
        delete_game_from_dictionary(interaction)
        return 
    elif game_status == "tie":
        # we need to send to database that game is finished
        finish_game_aka_delete_user_from_table(interaction, game.game_id)
        embed = create_embed(game, game_variables, interaction)
        view = ButtonGrid(game.board)
        await interaction.response.edit_message(embed=embed, view=view)
        await interaction.followup.send("It's a tie!")
        delete_game_from_dictionary(interaction)
        return
    
    embed = create_embed(game, game_variables, interaction)
    view = ButtonGrid(game.board, lock_buttons=True) if game.last_move_player == "bot" else ButtonGrid(game.board)
    await interaction.response.edit_message(embed=embed, view=view)

    if result:
        await interaction.followup.send(result)
        game.reset()
    
    # After updating for the player's move
    if game.last_move_player == "bot": # if player is last, then bot should move now
        shiro_move(interaction, difficulty, game)

        # Update the game state and visuals again for the bot's move
        embed = create_embed(game, game_variables, interaction)
        view = ButtonGrid(game.board, lock_buttons=False)
        
        game_status = game.game_status
        if game_status == "finished":
            # we need to send to database that game is finished
            finish_game_aka_delete_user_from_table(interaction, game.game_id)
            embed = create_embed(game, game_variables, interaction)
            view = ButtonGrid(game.board)
            await interaction.followup.send(embed=embed, view=view)
            await interaction.followup.send(str(game.who_won))
            delete_game_from_dictionary(interaction)
            return
             
        elif game_status == "tie":
            # we need to send to database that game is finished
            finish_game_aka_delete_user_from_table(interaction, game.game_id)
            embed = create_embed(game, game_variables, interaction)
            view = ButtonGrid(game.board)
            await interaction.followup.send(embed=embed, view=view)
            await interaction.followup.send("It's a tie!")
            delete_game_from_dictionary(interaction)
            return
        await interaction.followup.send(embed=embed, view=view)
        # Delete the game instance from the dictionary for both finished and tie condition


def create_embed(game, game_variables=None, interaction=None):
    bot_name = get_bot_name_from_context(interaction) if interaction else "Bot"
    
    # Assuming game.board is a 2D list
    board_desc = f"""Game status is: {game.game_status}\n
    {bot_name}: {game.bot_last_response}\n
    Your turn, {game.last_move_player}! Your mark: {game.player_mark}
     """
    
    embed = discord.Embed(title="Tic Tac Toe", description=board_desc, color=0x3498db)
    
    return embed

def set_game_state(game, game_variables):
    """Sets the game state based on the given game variables."""
    game.set_board_from_state(game_variables["board_state"])
        # we need to take the last move player from db to determine if it i
    game.set_last_move_player(game_variables["last_move_player"])
    game.set_player_mark(game_variables["player_mark"])
    game.set_game_id(game_variables["game_id"])
    game.set_game_status(game_variables["game_status"])
    #game.set_bot_last_response(game_variables["bot_last_response"])
    game.set_difficulty(game_variables["difficulty"])


def get_moves_from_algorithm(game, player_mark):
    """Returns the best moves for the given board and player mark."""
    # Create a 2D board and get the best move for bot using the Minimax function
    best_moves_from_master = game.find_best_moves(game.board, player_mark)

    best_move = None
    second_best = None
    third_best = None

    if len(best_moves_from_master) >= 1:
        best_move = best_moves_from_master[0]
    if len(best_moves_from_master) >= 2:
        second_best = best_moves_from_master[1]
    if len(best_moves_from_master) == 3:
        third_best = best_moves_from_master[2]

    return best_move, second_best, third_best


def shiro_move(interaction, difficulty, game):
    user_id = interaction.user.id
    if user_id not in games:
        games[user_id] = TicTacToe()
    # Set a local reference to the user's game instance
    game = games[user_id]

    game_variables = get_game_variables(interaction, difficulty) # retrive game status from database
        # Create a 2D board and get the best move for bot using the Minimax function
    best_move, second_best, third_best = get_moves_from_algorithm(game, 'O')
# The _ ignores the row, you only get the column    # Convert 2D position to flat position
    print(best_move, second_best, third_best)
    print(f"bot move position: {third_best}")
    set_game_state(game, game_variables)
        # You'll need to implement this
    which_move = random.randint(0, 2)

    # HERE WE SEND IT TO CHATGPT TO GET ANSWER
    shiro_comment, shiro_move = get_shiro_response_on_tictactoe(interaction, game, best_move, second_best, third_best)
    game.set_bot_last_response(shiro_comment)
    #################################################################
    if best_move == shiro_move or second_best == shiro_move or third_best == shiro_move:
        game.make_move(shiro_move, shiro_comment)

    else:
        # Handle the case where the chosen move is None.
        # If something in bot answer went wrong, just choose best move.
        game.make_move(best_move, "Hmm, I think I will go for the best move!")
        print("Defaulted to best move, something went wrong with bot answer")

def delete_game_from_dictionary(interaction):
    user_id = interaction.user.id
    if user_id in games:
        del games[user_id]
        print("Deleted game instance from dictionary")



async def start_tic_tac_toc(interaction, difficulty):
    user_id = interaction.user.id
    if user_id not in games:
        games[user_id] = TicTacToe()

    # Set a local reference to the user's game instance
    game = games[user_id]
    game.set_interaction(interaction)
    
        #1. we need to first determine who starts first if this is new game, then we will send to DB and check
    who_starts_first = random.randint(0, 1)
    

    last_move_player="player" if who_starts_first == 0 else "bot"
    # FOR TESTING PURPOSES
    #last_move_player = "player"
        # 2. Retrieve the game status from the database
    game_variables = get_game_variables(interaction, difficulty, last_move_player)
#####################################################################################
# I NEED TO CHECK WHO IS GOONA MOVE FIRST AND IF bot, THEN SEND TO API FOR bot MOVE AND TRIGGER MOVE FUNCTION 
    print(f"game varuables: {game_variables}")
    if game_variables is None:
        # Handle the error, e.g., by sending a message or logging it
        await interaction.response.send_message("An error occurred while retrieving the game data.")
        return

    # 2. Set the game board based on the retrieved game state and difficulty
    if difficulty not in ["easy", "medium", "hard"]:  # need to change it to droplist
        # set default difficulty to medium
        difficulty = "medium"
    set_game_state(game, game_variables)
 
    print(f"Board: {game.board}")
    if not isinstance(game.board, list) or len(game.board) != 9:
        print("Board is not in the expected format!")
    required_keys = ["game_status", "difficulty", "last_move_player", "player_mark"]
    if not all(key in game_variables for key in required_keys):
        print("Some keys are missing from game_variables!")

    # 3. Create and send the embed
    embed = create_embed(game, game_variables, interaction)
    view = ButtonGrid(game.board, lock_buttons=True) if game.last_move_player == "bot" else ButtonGrid(game.board)
    await interaction.response.send_message(embed=embed, view=view)
    if game.last_move_player == "bot": # if player is last, then bot should move now

        shiro_move(interaction, difficulty, game) # bot makes its move
        # Update the game state and visuals again for the bot's move
        embed = create_embed(game, game_variables, interaction)
        view = ButtonGrid(game.board, lock_buttons=False)
        await interaction.followup.send(embed=embed, view=view)
