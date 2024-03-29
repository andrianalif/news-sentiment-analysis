from flask import Flask, render_template, request, jsonify, Response, send_file
from flask_sqlalchemy import SQLAlchemy
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from io import StringIO
from collections import Counter
from textblob import TextBlob
from flask_executor import Executor
from csv_utils import create_csv
from sentiment_analysis import classify_sentiment
import requests
import re
import csv
import nltk
import matplotlib.pyplot as plt
import base64
import pandas as pd

app = Flask(__name__, template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://@LAPTOP-4NMFI42A/extract_db?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['EXECUTOR_TYPE'] = 'thread'
app.config['EXECUTOR_MAX_WORKERS'] = 2
executor = Executor(app)
db = SQLAlchemy(app)

class ExtractedData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(2048), nullable=False)
    keyword = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<ExtractedData {self.url}>'
class NewsSite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(2048), nullable=False, unique=True)

    def __repr__(self):
        return f'<NewsSite {self.url}>'

# Buat tabel database jika belum ada dengan konteks aplikasi
with app.app_context():
    db.create_all()

# Fungsi untuk membersihkan dan memisahkan teks menjadi kalimat
def tokenize_sentences(text):
    text = re.sub(r'[^a-zA-Z\s]', '', text).lower()
    return nltk.tokenize.sent_tokenize(text)

def clean_text(text, min_sentence_length=40):
    # Konversi huruf kecil
    text = text.lower()

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
    unwanted_phrases = ['All rights reserved', 'All right reserved', 'Ad Feedback', 'ADVERTISEMENT SCROLL TO CONTINUE WITH CONTENT', 'MINING.COM', 'Advertise', "Buyer's", 'RSS', 'Education']
    for phrase in unwanted_phrases:
        text = text.replace(phrase, '')

    # Menghilangkan karakter non-alfabetik kecuali tanda baca penting
    # Tetap mempertahankan angka yang memberikan informasi
    text = re.sub(r'[^a-zA-Z0-9.,;!?\'\`$]', ' ', text)

    # Tokenisasi kalimat
    sentences = nltk.tokenize.sent_tokenize(text)

    # Menghapus kalimat yang terlalu pendek yang mungkin tidak penting
    cleaned_sentences = []
    for sentence in sentences:
        if len(sentence) > min_sentence_length:
            # Memeriksa sentimen kalimat
            sentiment = classify_sentiment(sentence)
            # Menambahkan kalimat ke list jika relevan (positif atau negatif)
            if sentiment in ['positive', 'negative']:
                cleaned_sentences.append(sentence)

    # Menggabungkan kalimat yang bersih menjadi teks yang dibersihkan
    cleaned_text = ' '.join(cleaned_sentences)

    return cleaned_text

def create_and_save_chart(positive_percentage, negative_percentage, filename):
    labels = ['Positive', 'Negative']
    sizes = [positive_percentage, negative_percentage]
    colors = ['#008000', '#FF0000']
    
    plt.figure(figsize=(8, 8))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors)
    plt.axis('equal')  
    plt.title('Sentiment Percentage')
    plt.savefig(filename)
    plt.close()
    
def get_top_nouns(text, n=5):
    words = nltk.word_tokenize(text)
    tagged_words = nltk.pos_tag(words)
    nouns = [word for word, pos in tagged_words if pos.startswith('NN')]
    top_nouns = Counter(nouns).most_common(n)
    return top_nouns

@app.route('/', methods=['GET'])
def home():
    return render_template('home.html')

def get_absolute_url(base, link):
    if not link:
        return None
    if '://' not in link:
        return urljoin(base, link)
    return link

visited_links = set()

@app.route('/extract', methods=['POST'])
def extract():
    keywords_input = request.form.get('keyword').lower()
    keywords = keywords_input.split(',')  # Pisahkan kata kunci dengan koma

    if len(keywords) > 5:
        return jsonify({'error': 'Maximum 5 keywords allowed.'}), 400
    
    try:
        news_sites = NewsSite.query.all()

        for news_site in news_sites:
            site_url = news_site.url
            future = executor.submit(do_extraction_task, site_url, keywords)
            result = future.result()  # Menunggu hasil ekstraksi
            if 'error' in result:
                return jsonify(result), 500

        return render_template('extract_result.html', message='Extraction process completed successfully.'), 200
    except Exception as e:
        error = str(e)
        print(f"Error in extract function: {error}")
        return jsonify({'error': error}), 500

def do_extraction_task(site_url, keywords):
    response = requests.get(site_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        extracted_data = []  # Inisialisasi daftar untuk menyimpan data yang diekstraksi

        for keyword in keywords:
            links = soup.find_all('a', href=True)
            for link in links:
                link_text = link.get_text(strip=True).lower()
                link_url = link['href']
                link_url = get_absolute_url(site_url, link_url)
                if link_url and keyword in link_text and link_url not in visited_links:
                    visited_links.add(link_url)
                    
                    try:
                        link_response = requests.get(link_url)
                        if link_response.status_code == 200:
                            link_soup = BeautifulSoup(link_response.content, 'html.parser')
                            texts = ' '.join([t for t in link_soup.stripped_strings])
                            if keyword in texts.lower():
                                new_data = ExtractedData(url=link_url, keyword=keyword, content=texts)
                                db.session.add(new_data)
                                db.session.commit()
                                extracted_data.append(new_data)  # Tambahkan data yang diekstraksi ke daftar
                    except requests.exceptions.RequestException as e:
                        print(f"Failed to retrieve content from {link_url}: {e}")

        return extracted_data

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

@app.route('/download_sentence_sentiments', methods=['GET', 'POST'])
def download_sentence_sentiments():
    # Menggunakan group_by() bersama dengan distinct() untuk mendapatkan hasil unik
    news_sites = db.session.query(ExtractedData.url).group_by(ExtractedData.url).all()

    # Lakukan iterasi untuk setiap situs berita
    with pd.ExcelWriter('data.xlsx') as writer:
        for site in news_sites:
            site_name = site.url.split('//')[-1].split('/')[0]  # Mendapatkan nama situs dari URL
            site_data = ExtractedData.query.filter_by(url=site.url).all()

            # Gabungkan semua teks yang diekstraksi dari situs berita menjadi satu teks
            combined_text = ' '.join([clean_text(data.content) for data in site_data])

            # Pisahkan teks menjadi kalimat
            sentences = nltk.tokenize.sent_tokenize(combined_text)

            # Hitung sentimen
            positive_count = sum(1 for sentence in sentences if classify_sentiment(sentence) == 'positive')
            negative_count = sum(1 for sentence in sentences if classify_sentiment(sentence) == 'negative')
            total_sentences = len(sentences)
            if total_sentences != 0:
                positive_percentage = (positive_count / total_sentences) * 100
                negative_percentage = (negative_count / total_sentences) * 100
            else:
                positive_percentage = 0
                negative_percentage = 0

            # Membuat nama file untuk chart
            chart_filename = f"{site_name}_sentiment_chart.png"

            # Membuat dan menyimpan grafik
            create_and_save_chart(positive_percentage, negative_percentage, chart_filename)

            # Membaca gambar chart sebagai file biner
            with open(chart_filename, 'rb') as f:
                chart_data = f.read()

            # Encode gambar chart sebagai Base64
            chart_base64 = base64.b64encode(chart_data).decode('utf-8')

            # Membuat data untuk CSV
            csv_data = {
                'Sentiment': ['Positive', 'Negative'],
                'Percentage': [f"{round(positive_percentage, 2)}%", f"{round(negative_percentage, 2)}%"]
            }
            top_nouns = get_top_nouns(combined_text)
            sentences_data = [{'Sentence': sentence, 'Sentiment': classify_sentiment(sentence)} for sentence in sentences]

            # Menulis data ke dalam file Excel dengan multiple sheets
            pd.DataFrame(csv_data).to_excel(writer, sheet_name=f'{site_name} - Sentiment', index=False)
            pd.DataFrame({'Top Nouns': [noun[0] for noun in top_nouns]}).to_excel(writer, sheet_name=f'{site_name} - Top Nouns', index=False)
            pd.DataFrame(sentences_data).to_excel(writer, sheet_name=f'{site_name} - Sentences', index=False)

            # Tautkan gambar chart ke dalam file Excel
            chart_df = pd.DataFrame({'Chart': [chart_base64]})
            chart_df.to_excel(writer, sheet_name=f'{site_name} - Chart Image', index=False)

    return send_file('data.xlsx', as_attachment=True)

@app.route('/download_sentiment_chart', methods=['GET'])
def download_sentiment_chart():
    return send_file('sentiment_chart.png', as_attachment=True)

@app.route('/save_news_site', methods=['POST'])
def save_news_site():
    data = request.json
    site_url = data.get('url')

    if not site_url:
        return jsonify({'error': 'Missing URL parameter'}), 400

    # Cek apakah situs berita sudah ada dalam database
    existing_site = NewsSite.query.filter_by(url=site_url).first()
    if existing_site:
        return jsonify({'error': 'News site already exists in the database'}), 400

    # Simpan situs berita ke dalam database
    new_site = NewsSite(url=site_url)
    db.session.add(new_site)
    db.session.commit()

    return jsonify({'message': 'News site saved successfully'}), 201

if __name__ == '__main__':
    app.run(debug=True)