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

def get_journal_feedback(entry_content):
    """
    Use Ollama TinyLLaMA to analyze a journal entry and return motivational feedback.
    """
    prompt = (
        "A user has written the following journal entry:\n\n"
        f"{entry_content}\n\n"
        "Start your response with 'My dear friend,' and ensure the tone is warm, supportive, and gentle throughout. "
        "DO NOT include any formal greetings like 'Dear user' or 'Dear journal entry.' "
        "DO NOT sign off with 'Respectfully yours,' 'Best regards,' or any other formal ending. "
        "The message should be full of encouragement, motivational tips, and practical mental health advice. "
        "Keep the response entirely informal, loving, and focused on healing, without any sign-offs or formalities."
    )

    try:
        response = ollama.chat(
            model='tinyllama',
            messages=[
                {'role': 'user', 'content': prompt}
            ]
        )
        return response['message']['content']
    except Exception as e:
        return f"An error occurred while generating journal feedback: {e}"
