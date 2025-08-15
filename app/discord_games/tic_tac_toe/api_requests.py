# Note: you need to be using OpenAI Python v0.27.0 for the code below to work
import dis
import re

import openai
from openai import OpenAI
from app.utils.ai_related.groq_api import send_to_groq
client = OpenAI()

import threading

class APIResponse:
    def __init__(self):
        self.response = None
        self.error = None


def get_shiro_response_on_tictactoe(interaction, game, best_move, second_best, third_best):
    print("gamevariables recived in api request: " + str(game))
    discord_username = format_discord_username(interaction.user.name)
    #board_state_str = ''.join(game.board) 
    shiro_last_response = game.bot_last_response
    moves_info = ""
    if best_move is not None:
        moves_info += f"best possible move: position '{best_move}'."
    if second_best is not None:
        moves_info += f"second best move: position '{second_best}'."
    if third_best is not None:
        moves_info += f"third best move: position '{third_best}'."

    game_information_for_master = f"""
    This is current board state: {game.board}
    You are playing as: '{game.player_mark}' and now it is your turn to make a move.
    Here are moves that were calculated by algorithm :
    {moves_info}.
    Difficulty user chose: '{game.difficulty}' This is important for you to know because it will affect your decisions.
    This is your last comment, use it to make follow up comment: {shiro_last_response}.
    What i want for you is to decide what move you want to make based on the difficulty the user choose.
    I want you to take a short break, think about it, and then make your decision.
    Oh, and don't mention about algorithm, it's our secret. Pretend it is your own choice.
    Please, answer in this format:
    position: choose one of the moves above
    comment: comment about your move strategy. Make it playful and engaging. But keep it short.
    """

    shiros_decision = [
        {"role": "system", "content": f"""Right now you are on discord and you are playing tic tac toe game with user: '{discord_username}'"""},
        {"role": "system", "content": game_information_for_master}
    ]



    print("messages: " + str(shiros_decision))
    what_shiro_chose = send_to_groq(shiros_decision)
    
    print(f"bot made this decision:\n {what_shiro_chose}")
    # Extract the move position using regex
    # match = re.search(r'Best possible move: (\d)', what_shiro_chose)
    # if match:
    #     move_position = int(match.group(1))
    # else:
    #     print("Failed to extract move position from response")
    #     # we will need to resend it to master

    

    

    # Check if the response is a tuple
    if isinstance(what_shiro_chose, tuple):
        # Extract the first element of the tuple which should be the string response
        what_shiro_chose = what_shiro_chose[0]
    
    if isinstance(what_shiro_chose, str):
        # Extract position number
        move_match = re.search(r'position:\s*(\d+)', what_shiro_chose, re.IGNORECASE)
        shiro_move = int(move_match.group(1)) if move_match else None

        # Extract comment
        comment_match = re.search(r'comment:\s*"((?:\\.|[^"\\])*)"', what_shiro_chose, re.IGNORECASE | re.DOTALL)
        if not comment_match:
            comment_match = re.search(r'comment:\s*(.*)', what_shiro_chose, re.IGNORECASE | re.DOTALL)
        
        shiro_comment = comment_match.group(1).strip() if comment_match else None

        print("-------------")
        print("Bot Comment:", shiro_comment)
        print("Next Move:", shiro_move)
        print("-------------")
        
        return shiro_comment, shiro_move
    else:
        print("Received non-string response from OpenAI.")
        return None, None

          
    

    

    
def api_call_thread(api_response, messages, temperature, model):
    try:
        completion = client.chat.completions.create(model=model,
        messages=messages,
        temperature=temperature)
        if completion.choices:
            api_response.response = completion.choices[0].message.content
        else:
            print("completion.choices is empty!")
            api_response.error = "completion.choices is empty!"
    except openai.APIError as e:
        api_response.error = f"OpenAI API returned an API Error: {e}"
    except openai.error.RateLimitError as e:
        api_response.error = f"OpenAI API request exceeded rate limit: {e}"
    except openai.error.APIConnectionError as e:
        if 'timed out' in str(e):
            api_response.error = "Request to OpenAI API timed out"
        else:
            api_response.error = f"Error: {e.args[0]}"



def extract_position_from_response(answer):
    pass
#   #completion_tokens = result[2] or _,_,completion_tokens,_ = result if i would like ot take only one

def format_discord_username(discord_username):
    """Removes special characters from a discord username and converts it to lowercase"""
    discord_username = discord_username.lower()
    print("discord_username: " + discord_username)
    if discord_username == '._.shiro._.':
        sanitized_username = "AI Shiro"
    else:
        sanitized_username = re.sub(r'[^a-zA-Z0-9]', '', discord_username)

    return sanitized_username


def board_string_to_formatted(board_str):
        formatted_board = ''
        for i in range(0, 9, 3):
            formatted_board += board_str[i:i+3] + '\n'
        return formatted_board.strip()

if __name__ == "__main__":
    
    pass
    
