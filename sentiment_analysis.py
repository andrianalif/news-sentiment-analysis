import nltk
from textblob import TextBlob

# Fungsi untuk mengklasifikasikan sentimen
def classify_sentiment(sentence):
    analysis = TextBlob(sentence)
    polarity = analysis.sentiment.polarity
    # Tentukan ambang batas di mana di atasnya dianggap positif(1) dan di bawahnya negatif(-1)
    threshold = -0.05
    if polarity >= threshold:
        return 'positive'
    else:
        return 'negative'