# app/controllers/services/recommendations.py

import ollama

def get_llama_recommendation(user_input):
    """
    Send user's survey answers to the local TinyLLaMA model running via Ollama
    and get mental health recommendations.
    """
    prompt = f"Based on this user's input, provide a mental health support recommendation:\n\n{user_input}\n\nRespond clearly and empathetically."

    try:
        response = ollama.chat(
            model='tinyllama',
            messages=[
                {'role': 'user', 'content': prompt}
            ]
        )
        return response['message']['content']
    except Exception as e:
        return f"An error occurred while generating the recommendation: {e}"


