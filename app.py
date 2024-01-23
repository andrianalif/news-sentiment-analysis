from flask import Flask, render_template, request, render_template_string, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from io import StringIO
from collections import Counter
from textblob import TextBlob
import requests
import re
import csv
import nltk

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///extract.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Model Database
class ExtractedData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(2048), nullable=False)
    keyword = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<ExtractedData {self.url}>'

# Buat tabel database jika belum ada dengan konteks aplikasi
with app.app_context():
    db.create_all()
    
@app.route('/', methods=['GET'])
def home():
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>News Sentiment Analysis</title>
            <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
        </head>
        <body>
            <div class="wrapper">
                <div class="box">
                    <img src="{{ url_for('static', filename='pama.png') }}" alt="Logo" class="logo">
                    <h1 class="unselectable">News Sentiment Analysis</h1>
                    <form id="mainForm" method="post">
                        <div class="news-url">
                            <label for="url">News URL:</label>
                            <input type="text" id="url" name="url" required>
                            <label for="keyword">Keyword:</label>
                            <input type="text" id="keyword" name="keyword" required>
                        </div>
                        <button type="submit" class="analyze" formaction="/extract">Extract</button>
                    </form>
                    <form id="mainForm2" method="get>
                        <button type="submit" class="download" formaction="/download_sentence_sentiments">Download</button>
                    </form>
                </div>
            </div>

            <script>
            function setActionAndSubmit(action) {
                var form = document.getElementById('mainForm');
                form.action = action;
                form.submit();
            }
            </script>
        </body>
        </html>
    ''')

visited_links = set()  # Set untuk melacak link yang sudah dikunjungi

def get_absolute_url(base, link):
    if not link:
        return None
    if '://' not in link:
        return urljoin(base, link)
    return link

@app.route('/extract', methods=['POST'])
def extract():
    site_url = request.form.get('url')
    keywords_input = request.form.get('keyword').lower()
    keywords = keywords_input.split(',')  # Pisahkan kata kunci dengan koma

    if len(keywords) > 5:
        return jsonify({'error': 'Maksimal 5 kata kunci yang diperbolehkan.'}), 400
    
    try:
        response = requests.get(site_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            extracted_info = []
            links_visited = 0  # Inisialisasi penghitung link
            new_links_found = False  # Flag untuk melacak apakah ada link baru yang dikunjungi

            for keyword in keywords:  # Iterasi melalui setiap kata kunci
                links = soup.find_all('a', href=True)
                for link in links:
                    link_text = link.get_text(strip=True).lower()
                    link_url = link['href']
                    link_url = get_absolute_url(site_url, link_url)
                    if link_url and keyword in link_text and link_url not in visited_links:
                        new_links_found = True
                        visited_links.add(link_url)  # Tandai link ini sebagai dikunjungi
                        links_visited += 1  # Inkremen setiap kali mengunjungi link
                        
                        try:
                            link_response = requests.get(link_url)
                            if link_response.status_code == 200:
                                link_soup = BeautifulSoup(link_response.content, 'html.parser')
                                texts = ' '.join([t for t in link_soup.stripped_strings])
                                if keyword in texts.lower():
                                    extracted_info.append({'url': link_url, 'text': link_text, 'full_text': texts, 'keyword': keyword})
                        except requests.exceptions.RequestException as e:
                            # Handle exceptions for each link request here
                            print(f"Failed to retrieve content from {link_url}: {e}")

            # Cek apakah ada link baru yang dikunjungi
            if not new_links_found:
                return jsonify({'message': 'All links have been visited'}), 200

            # Simpan ke database
            try:
                for data in extracted_info:
                    new_data = ExtractedData(url=data['url'], keyword=data['keyword'], content=data['full_text'])
                    db.session.add(new_data)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                return jsonify({'error': str(e)}), 500

            # Tambahkan jumlah link yang dikunjungi ke response
            return jsonify({
                'extracted_info': extracted_info,
                'links_visited': links_visited
            })
    except requests.exceptions.MissingSchema:
        return jsonify({'error': 'Invalid URL scheme provided.'}), 400
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Failed to retrieve content from the URL: {e}'}), 400
    
@app.route('/data/<int:data_id>')
def get_data(data_id):
    data = ExtractedData.query.get_or_404(data_id)
    return jsonify({
        'url': data.url,
        'keyword': data.keyword,
        'content': data.content
    })
    
@app.route('/show_data')
def show_data():
    all_data = ExtractedData.query.all()
    return render_template('data.html', data_list=all_data)

# Fungsi untuk membersihkan dan memisahkan teks menjadi kalimat
def tokenize_sentences(text):
    text = re.sub(r'[^a-zA-Z\s]', '', text).lower()
    return nltk.tokenize.sent_tokenize(text)

# Fungsi untuk mengklasifikasikan sentimen
def classify_sentiment(sentence):
    analysis = TextBlob(sentence)
    polarity = analysis.sentiment.polarity
    # Tentukan ambang batas di mana di atasnya dianggap positif(1) dan di bawahnya negatif(-1)
    threshold = 0
    if polarity >= threshold:
        return 'positive'
    else:
        return 'negative'

def clean_text(text, min_sentence_length=40):
    # Identifikasi dan hilangkan teks di antara tag HTML khusus
    title_match = re.search(r'<title[^>]*>(.*?)<\/title>', text, re.IGNORECASE | re.DOTALL)
    script_match = re.search(r'<script[^>]*>(.*?)<\/script>', text, re.IGNORECASE | re.DOTALL)

    if title_match:
        title_text = title_match.group(1)
        text = text.replace(title_text, '')

    if script_match:
        script_text = script_match.group(1)
        text = text.replace(script_text, '')

    # Menghilangkan kata yang berada di depan ".com" dan ".com" itu sendiri
    text = re.sub(r'\b\S+\.com\b|\b\S+\b(?=\s*\.com)', '', text)

    # Menghilangkan URL
    text = re.sub(r'http\S+|www\S+', '', text)

    # Menghilangkan kata-kata yang tidak diinginkan
    unwanted_phrases = ['All rights reserved', 'All right reserved', 'ADVERTISEMENT SCROLL TO CONTINUE WITH CONTENT']
    for phrase in unwanted_phrases:
        text = text.replace(phrase, '')

    # Menghilangkan karakter non-alfabetik kecuali tanda baca penting
    text = re.sub(r'[^a-zA-Z0-9.,;!?\'\`]', ' ', text)

    # Tokenisasi kalimat
    sentences = nltk.tokenize.sent_tokenize(text)

    # Menghapus kalimat yang terlalu pendek yang mungkin tidak penting
    sentences = [s for s in sentences if len(s) > min_sentence_length]

    # Mengganti whitespace berlebih dengan satu spasi
    cleaned_text = ' '.join(sentences)

    return cleaned_text

@app.route('/download_sentence_sentiments', methods=['GET', 'POST'])
def download_sentence_sentiments():
    all_data = ExtractedData.query.all()
    combined_text = ' '.join([clean_text(data.content) for data in all_data])

    # Pisahkan teks menjadi kalimat
    sentences = nltk.tokenize.sent_tokenize(combined_text)

    # Hitung sentimen
    sentiment_counts = Counter([classify_sentiment(sentence) for sentence in sentences])
    total_sentences = len(sentences)

    # Hitung persentase
    sentiment_percentages = {sentiment: (count / total_sentences) * 100 for sentiment, count in sentiment_counts.items()}

    # Membuat data CSV
    si = StringIO()
    cw = csv.writer(si)
    
    # Tulis persentase sentimen ke CSV
    cw.writerow(['Sentiment', 'Percentage'])
    for sentiment, percentage in sentiment_percentages.items():
        cw.writerow([sentiment, f"{round(percentage, 2)}%"])
    cw.writerow(['', ''])  # Baris kosong sebagai pemisah

    # Tulis kalimat dan sentimennya
    cw.writerow(['Sentence', 'Sentiment'])
    for sentence in sentences:
        sentiment = classify_sentiment(sentence)
        cw.writerow([sentence, sentiment])

    output = si.getvalue()
    return Response(output, mimetype="text/csv", headers={"Content-disposition": "attachment; filename=sentence_sentiments.csv"})

if __name__ == '__main__':
    app.run(debug=True)