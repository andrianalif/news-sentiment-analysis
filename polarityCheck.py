from textblob import TextBlob

def classify_sentiment(sentence):
    analysis = TextBlob(sentence)
    polarity = analysis.sentiment.polarity
    # Tentukan ambang batas di mana di atasnya dianggap positif(1) dan di bawahnya negatif(-1)
    threshold = 0
    if polarity >= threshold:
        sentiment = 'positive'
    else:
        sentiment = 'negative'
    print(f"Polaritas kalimat: {polarity}")
    return sentiment

# Contoh penggunaan
sentence = "more than 100 people were killed during the chaos, where israeli troops opened fire and triggered panic as hungry palestinian civilians were gathering around food aid trucks, palestinian officials and eyewitnesses said."
sentiment = classify_sentiment(sentence)
print(f"Sentimen: {sentiment}")  # Output: positive