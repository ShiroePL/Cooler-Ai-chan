from app.utils.groq_api import send_to_groq


def ask_function(question: str) -> str:
    response = send_to_groq([{"role": "user", "content": question}])
    return response[0]

def chat_function(messages: List[str]) -> str:
    response = send_to_groq([{"role": "user", "content": messages}])
    return response[0]
