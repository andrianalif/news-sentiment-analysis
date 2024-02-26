from flask import Flask, render_template, request, jsonify, Response, send_file
from flask_sqlalchemy import SQLAlchemy
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from io import StringIO
from collections import Counter
from textblob import TextBlob
from flask_executor import Executor
import requests
import re
import csv
import nltk
import matplotlib.pyplot as plt
import base64

app = Flask(__name__, template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://@LAPTOP-4NMFI42A/extract_db?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['EXECUTOR_TYPE'] = 'thread'
app.config['EXECUTOR_MAX_WORKERS'] = 2
executor = Executor(app)
db = SQLAlchemy(app)

# Model Database
class ExtractedData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(2048), nullable=False)
    keyword = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<ExtractedData {self.url}>'
    
# Definisikan model NewsSite di sini
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
    unwanted_phrases = ['All rights reserved', 'All right reserved', 'ADVERTISEMENT SCROLL TO CONTINUE WITH CONTENT', 'MINING.COM', 'Advertise', "Buyer's", 'RSS', 'Education']
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

def create_and_save_chart(positive_percentage, negative_percentage):
    labels = ['Positive', 'Negative']
    sizes = [positive_percentage, negative_percentage]
    
    plt.figure(figsize=(8, 8))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=['green', 'red'])
    plt.axis('equal')  
    plt.title('Sentiment Percentage')
    plt.savefig('sentiment_chart.png')  
    plt.close()

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
        # Ambil semua URL situs berita dari database
        news_sites = NewsSite.query.all()

        for news_site in news_sites:
            site_url = news_site.url
            future = executor.submit(do_extraction_task, site_url, keywords)
            result = future.result()  # Menunggu hasil ekstraksi
            if 'error' in result:
                return jsonify(result), 500  # Jika ada error, kembalikan response dengan kode 500

        return jsonify({'message': 'Extraction process completed successfully.'}), 200
    except Exception as e:
        error = str(e)
        print(f"Error in extract function: {error}")
        return jsonify({'error': error}), 500

def do_extraction_task(site_url, keywords):
    response = requests.get(site_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        extracted_info = []
        links_visited = 0  # Inisialisasi penghitung link
        new_links_found = False  # Flag untuk melacak apakah ada link baru yang dikunjungi
        keyword_found = False  # Flag untuk melacak apakah ada keyword yang ditemukan

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
                                keyword_found = True
                                # Simpan ke database
                                try:
                                    new_data = ExtractedData(url=link_url, keyword=keyword, content=texts)
                                    db.session.add(new_data)
                                    db.session.commit()
                                except Exception as e:
                                    db.session.rollback()
                                    return jsonify({'error': str(e)}), 500
                    except requests.exceptions.RequestException as e:
                        # Handle exceptions for each link request here
                        print(f"Failed to retrieve content from {link_url}: {e}")

        # Cek apakah tidak ada link baru yang ditemukan
        if not new_links_found:
            return 'All links have been visited'

        # Cek apakah tidak ada keyword yang ditemukan
        if not keyword_found:
            return 'There is no keyword you are looking for'

        # Jika tidak ada kondisi khusus yang terpenuhi, kembalikan pesan bahwa ekstraksi berhasil
        return 'Extraction process completed successfully.'


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
    all_data = ExtractedData.query.all()
    
    # Gabungkan semua teks yang diekstraksi menjadi satu teks
    combined_text = ' '.join([clean_text(data.content) for data in all_data])

    # Pisahkan teks menjadi kalimat
    sentences = nltk.tokenize.sent_tokenize(combined_text)

    # Hitung sentimen
    positive_count = 0
    negative_count = 0
    
    # Cek apakah ada kalimat yang diekstraksi
    if sentences:
        for sentence in sentences:
            sentiment = classify_sentiment(sentence)
            if sentiment == 'positive':
                positive_count += 1
            elif sentiment == 'negative':
                negative_count += 1

        total_sentences = len(sentences)
        
        # Cek apakah total kalimat adalah nol
        if total_sentences != 0:
            positive_percentage = (positive_count / total_sentences) * 100
            negative_percentage = (negative_count / total_sentences) * 100
        else:
            positive_percentage = 0
            negative_percentage = 0
    else:
        # Jika tidak ada kalimat yang diekstraksi, atur persentase ke nol
        positive_percentage = 0
        negative_percentage = 0

    # Membuat dan menyimpan grafik
    create_and_save_chart(positive_percentage, negative_percentage)

    # Membaca gambar chart sebagai file biner
    with open('sentiment_chart.png', 'rb') as f:
        chart_data = f.read()

    # Encode gambar chart sebagai Base64
    chart_base64 = base64.b64encode(chart_data).decode('utf-8')
    
    # Mengumpulkan semua kata dari konten yang diekstraksi
    all_words = ' '.join([clean_text(data.content) for data in all_data]).split()

    # Hitung kemunculan kata-kata
    word_count = Counter(all_words)

    # Ambil 5 kata benda teratas
    top_nouns = [word for word, count in word_count.items() if nltk.pos_tag([word])[0][1] == 'NN'][:5]
   
    # Membuat data CSV
    si = StringIO()
    cw = csv.writer(si)
    
    # Tulis persentase sentimen ke CSV
    cw.writerow(['Sentiment', 'Percentage'])
    cw.writerow(['Positive', f"{round(positive_percentage, 2)}%"])
    cw.writerow(['Negative', f"{round(negative_percentage, 2)}%"])
    cw.writerow([]) 
    
    # Buat sheet baru untuk kata benda
    cw.writerow(['Top Nouns'])
    for noun in top_nouns:
        cw.writerow([noun])

    cw.writerow([])
    
    # Tulis kalimat dan sentimennya
    cw.writerow(['Sentence', 'Sentiment'])
    for sentence in sentences:
        sentiment = classify_sentiment(sentence)
        cw.writerow([sentence, sentiment])

    # Tautkan gambar chart ke dalam file CSV
    cw.writerow([])  # Baris kosong sebagai pemisah
    cw.writerow(['Chart Image'])
    cw.writerow(['Chart', chart_base64])

    # Reset posisi pointer di StringIO
    si.seek(0)

    # Mengonversi StringIO ke bytes
    output_bytes = si.getvalue().encode('utf-8')

    return Response(output_bytes, mimetype="text/csv", headers={"Content-disposition": "attachment; filename=sentence_sentiments.csv"})

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