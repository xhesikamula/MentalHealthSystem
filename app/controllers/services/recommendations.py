import ollama
import re
from langdetect import detect, detect_langs
from deep_translator import GoogleTranslator
from textblob import TextBlob


def detect_language(text):
    try:
        return detect(text)
    except:
        return "en"


def translate_to_english(text):
    return GoogleTranslator(source='auto', target='en').translate(text)


def translate_to_albanian(text):
    return GoogleTranslator(source='auto', target='sq').translate(text)


def get_llama_recommendation(user_input):
    lang = detect_language(user_input)

    # Translate Albanian input to English for processing
    if lang == 'sq':
        user_input_translated = translate_to_english(user_input)
    else:
        user_input_translated = user_input

    prompt = (
        "Based on this user's input, provide exactly 4 short and specific mental health "
        "recommendations to help them feel better. Format them as a numbered list (1) ..., 2) ..., etc). "
        "Keep each recommendation concise, actionable, and empathetic.\n\n"
        f"{user_input_translated}\n\n"
        "Respond clearly and kindly."
    )

    try:
        response = ollama.chat(
            model='tinyllama',
            messages=[{'role': 'user', 'content': prompt}]
        )
        result = response['message']['content']

        # Translate output back to Albanian if input was Albanian
        if lang == 'sq':
            result = translate_to_albanian(result)

        return result

    except Exception as e:
        return f"An error occurred while generating the recommendation: {e}"



def clean_signoffs(text):
    return re.sub(r"(Warmly|Sincerely|Best regards|With love|Respectfully|Ngrohtësisht|Me respekt|Your friend|[Yy]our name)[^\n]*", "", text).strip()



def is_positive_sentiment(text):
    """
    Detects if the sentiment of the given text is positive.
    If text is in Albanian, it translates to English first for accurate sentiment analysis.
    Returns True if polarity is above 0.2 (tweak threshold if needed).
    """
    try:
        lang = detect_language(text)
        if lang == 'sq':
            text = translate_to_english(text)
        blob = TextBlob(text)
        return blob.sentiment.polarity > 0.2
    except Exception as e:
        print(f"Sentiment analysis error: {e}")
        return False


def get_journal_feedback(entry_content):
    lang = detect_language(entry_content)

    if lang == 'sq':
        entry_content_translated = translate_to_english(entry_content)
    else:
        entry_content_translated = entry_content

    # ✅ If sentiment is positive, generate a personalized praise sentence via LLM
    if is_positive_sentiment(entry_content_translated):
        praise_prompt = (
            f"This is a journal entry from a user:\n\n"
            f"{entry_content_translated}\n\n"
            "The user seems to be doing well. Respond with one short and uplifting sentence "
            "to encourage and praise them. Be kind, direct, and personal. Do not include sign-offs."
        )

        try:
            response = ollama.chat(
                model='tinyllama',
                messages=[{'role': 'user', 'content': praise_prompt}]
            )
            result = response['message']['content']

            # ✅ Extract only the first sentence
            first_sentence = result.strip().split('.')[0].strip() + '.'
            cleaned_result = clean_signoffs(first_sentence)

            if lang == 'sq':
                cleaned_result = translate_to_albanian(cleaned_result)

            return cleaned_result

        except Exception as e:
            return f"An error occurred while generating positive feedback: {e}"

    # Otherwise: standard motivational tips
    prompt = (
        "A user wrote this journal entry:\n\n"
        f"{entry_content_translated}\n\n"
        "Reply with 4 very short, simple motivational sentences or tips. "
        "Use easy English words anyone can understand. "
        "Do NOT write explanations, stories, or philosophical ideas. "
        "Do NOT include greetings or sign-offs. "
        "Only write direct motivation and advice."
    )

    try:
        response = ollama.chat(
            model='tinyllama',
            messages=[{'role': 'user', 'content': prompt}]
        )
        result = response['message']['content']
        cleaned_result = clean_signoffs(result)

        if lang == 'sq':
            cleaned_result = translate_to_albanian(cleaned_result)

        return cleaned_result

    except Exception as e:
        return f"An error occurred while generating journal feedback: {e}"