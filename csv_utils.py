import pandas as pd
from sentiment_analysis import classify_sentiment

# Fungsi untuk membuat file CSV dan menulis data di dalamnya
def create_csv(site_name, data):
    # Data untuk ditulis ke dalam CSV
    csv_data = {
        'Sentiment': ['Positive', 'Negative'],
        'Percentage': [f"{round(data['positive_percentage'], 2)}%", f"{round(data['negative_percentage'], 2)}%"]
    }
    
    # Buat DataFrame untuk kata benda
    nouns_data = {'Top Nouns': [noun[0] for noun in data['top_nouns']]}
    nouns_df = pd.DataFrame(nouns_data)

    # Buat DataFrame untuk kalimat dan sentimennya
    sentences_data = {'Sentence': data['sentences'], 'Sentiment': [classify_sentiment(sentence) for sentence in data['sentences']]}
    sentences_df = pd.DataFrame(sentences_data)

    # Tautkan gambar chart ke dalam DataFrame
    chart_df = pd.DataFrame({'Chart': [data['chart_base64']]})

    # Buat file CSV dengan multiple sheets
    with pd.ExcelWriter(f'{site_name}_sentence_sentiments.xlsx') as writer:
        # Tulis data ke dalam sheets masing-masing
        pd.DataFrame(csv_data).to_excel(writer, sheet_name='Sentiment', index=False)
        nouns_df.to_excel(writer, sheet_name='Top Nouns', index=False)
        sentences_df.to_excel(writer, sheet_name='Sentences', index=False)
        chart_df.to_excel(writer, sheet_name='Chart Image', index=False)

    return f'{site_name}_sentence_sentiments.xlsx'