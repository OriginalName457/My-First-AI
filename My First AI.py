import openai
import os
import json
from googleapiclient.discovery import build
from collections import OrderedDict

# Initialize global variables
openai.api_key = "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"
GOOGLE_API_KEY = "AIzaSyCaCd2geSBJ1Yxar7wiF-S6hrQs6Kxjhqs"
CSE_ID = "41fec49dddba84b2f"
MODEL = "gpt-3.5-turbo"
PERSONA_DIRECTORY = r"C:\Users\13wie\OneDrive\Desktop\Workspace Realm"
CACHE_SIZE = 1000
cache = OrderedDict()

MAX_TOKENS = 4096
CHUNK_SIZE = 2048
default_messages = [
    {
        "role": "system",
        "content": "You are a helpful assistant."
    }
]

messages = default_messages.copy()

def get_persona_path(persona_name):
    return os.path.join(PERSONA_DIRECTORY, persona_name + '.json')

def load_persona(persona_name):
    global messages
    persona_path = get_persona_path(persona_name)
    if os.path.exists(persona_path):
        with open(persona_path, 'r') as f:
            messages = json.load(f)
        print(f"Loaded persona: {persona_name}")
    else:
        messages = default_messages.copy()
        print(f"No persona found for: {persona_name}")

def save_persona(persona_name):
    persona_path = get_persona_path(persona_name)
    with open(persona_path, 'w') as f:
        json.dump(messages, f)
    print(f"Saved persona: {persona_name}")

def delete_persona(persona_name):
    persona_path = get_persona_path(persona_name)
    if os.path.exists(persona_path):
        os.remove(persona_path)
        print(f"Deleted persona: {persona_name}")
    else:
        print(f"No persona found for: {persona_name}")

def create_response(user_input):
    total_response = ""
    while user_input:
        # Extract a chunk from the user input
        chunk = user_input[:CHUNK_SIZE]
        user_input = user_input[CHUNK_SIZE:]

        # Add chunk to messages
        messages.append({"role": "user", "content": chunk})

        # Keep the last CHUNK_SIZE messages
        messages_chunk = messages[-CHUNK_SIZE:]
        
        # Count the total tokens in our chunk
        total_tokens = sum([len(m['content']) for m in messages_chunk])

        # Ensure we don't exceed the max tokens of the model
        if total_tokens > MAX_TOKENS:
            over_tokens = total_tokens - MAX_TOKENS
            while over_tokens > 0 and len(messages_chunk) > 1:
                removed_message = messages_chunk.pop(0)
                over_tokens -= len(removed_message['content'])
        
        response = openai.ChatCompletion.create(
            model=MODEL, 
            temperature=0.2, 
            max_tokens=min(MAX_TOKENS - total_tokens, 1000),  # Set a larger limit on the response size
            messages=messages_chunk
        )

        if 'message' in response['choices'][0]:
            message = response['choices'][0]['message']
            messages.append({"role": "assistant", "content": message['content']})
            total_response += message['content']
            
    return total_response



def google_search(search_term, **kwargs):
    if search_term in cache:
        cache.move_to_end(search_term)
        return cache[search_term]
    service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
    res = service.cse().list(q=search_term, cx=CSE_ID, **kwargs).execute()
    result = res['items']
    cache[search_term] = result
    if len(cache) > CACHE_SIZE:
        cache.popitem(last=False)
    return result

def print_results(results):
    for result in results:
        print(result['title'])
        print(result['snippet'])
        print(result['link'], '\n')

def save_cache():
    with open('cache.json', 'w') as f:
        json.dump(list(cache.items()), f)

def load_cache():
    try:
        with open('cache.json', 'r') as f:
            cache_items = json.load(f)
        cache.update(cache_items)
    except FileNotFoundError:
        pass  # It's okay if the file doesn't exist yet

def start_chat():
    load_cache()
    persona_name = input("Enter persona name (or 'default' for no persona): ")
    load_persona(persona_name)

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            save_persona(persona_name)
            save_cache()
            break

        if user_input.lower().startswith('switch persona to '):
            save_persona(persona_name)
            persona_name = user_input[18:].strip()
            load_persona(persona_name)
            continue

        if user_input.lower().startswith('delete persona '):
            delete_persona_name = user_input[15:].strip()
            delete_persona(delete_persona_name)
            continue

        if "google this" in user_input.lower():
            search_query = user_input.replace("google this", "").strip()
            results = google_search(search_query)
            print_results(results)
            continue

        chatbot_response = create_response(user_input)

        if "I don't know" in chatbot_response:
            results = google_search(user_input)
            print_results(results)
        else:
            print('Chatbot: '+chatbot_response+'\n')

    print("Chat ended.")

start_chat()
