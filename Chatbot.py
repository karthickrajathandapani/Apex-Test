import requests

url = "http://localhost:11434/api/generate"

def chat_with_ollama(prompt):
    response = requests.post(url, json={
        "model": "llama3",
        "prompt": prompt,
        "stream": False
    })

    return response.json()['response']

while True:
    user_input = input("You: ")
    
    if user_input.lower() == "exit":
        break
    
    reply = chat_with_ollama(user_input)
    print("Bot:", reply)