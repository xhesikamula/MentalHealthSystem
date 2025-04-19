# sentiment_utils.py
from textblob import TextBlob

def analyze_sentiment(text):
    """
    Analyze sentiment of the given text using TextBlob.
    Returns:
        sentiment_type (str): 'positive', 'neutral', or 'negative'
        confidence_score (float): A score representing the confidence in sentiment classification
    """
    # Create a TextBlob object
    blob = TextBlob(text)

    # Perform sentiment analysis
    sentiment_score = blob.sentiment.polarity

    # Classify sentiment
    if sentiment_score > 0:
        sentiment_type = 'positive'
    elif sentiment_score < 0:
        sentiment_type = 'negative'
    else:
        sentiment_type = 'neutral'

    # Confidence score: absolute value of sentiment score (between 0 and 1)
    confidence_score = abs(sentiment_score)

    return sentiment_type, confidence_score
