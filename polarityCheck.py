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
sentence = "indiscriminate killing  the united nations is urging an investigation into indiscriminate israeli fire that killed half of a family in gaza after a cnn report on the attack was published wednesday."
sentiment = classify_sentiment(sentence)
print(f"Sentimen: {sentiment}")  # Output: positive