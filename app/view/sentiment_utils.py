from textblob import TextBlob

def analyze_sentiment(text):
    """
    Analyze the sentiment of a given text.
    Returns:
        sentiment_type (str): 'positive', 'neutral', or 'negative'
        confidence_score (float): polarity score between 0 and 1
    """
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity  # range: [-1.0, 1.0]

    if polarity > 0.1:
        sentiment = 'positive'
    elif polarity < -0.1:
        sentiment = 'negative'
    else:
        sentiment = 'neutral'

    confidence = round(abs(polarity), 2)  # Use absolute polarity as a basic confidence metric
    return sentiment, confidence
