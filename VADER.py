from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import requests
import re
import nltk
import string

app = Flask(__name__, template_folder='templates')
username = 'andri'
password = 'andri152002'
server = 'LAPTOP-4NMFI42A'
database_name = 'wikipedia_db'

app.config['SQLALCHEMY_DATABASE_URI'] = f'mssql+pyodbc://{username}:{password}@{server}/{database_name}?driver=ODBC+Driver+17+for+SQL+Server'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

analyzer = SentimentIntensityAnalyzer()

class ExtractedData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(2048), nullable=False)
    sentence = db.Column(db.Text, nullable=False)
    sentiment = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return f'<ExtractedData {self.url}>'
    
with app.app_context():
    db.create_all()

def get_absolute_url(base, link):
    if not link:
        return None
    if '://' not in link:
        return urljoin(base, link)
    return link

@app.route('/', methods=['GET'])
def home():
    return render_template('home.html')

@app.route('/extract', methods=['POST'])
def extract():
    site_url = request.form.get('url')

    if not site_url:
        return jsonify({'error': 'Missing URL parameter'}), 400
    
    try:
        extracted_data = do_extraction_task_from_url(site_url)
        if extracted_data is None:
            return render_template('extract_result.html', message='No data extracted. The keyword you input cannot be found, input another keyword!'), 404
        save_extracted_data(extracted_data)
        return render_template('extract_result.html', message='Extraction process completed successfully.'), 200
    except Exception as e:
        error = str(e)
        print(f"Error in extract function: {error}")
        return jsonify({'error': error}), 500

@app.route('/search', methods=['POST'])
def search():
    keyword = request.form.get('keyword')
    if not keyword:
        return jsonify({'error': 'Missing keyword parameter'}), 400

    search_url = f'https://en.wikipedia.org/wiki/{keyword}'
    extracted_data = do_extraction_task_from_url(search_url)
    if not extracted_data:
        return render_template('extract_result.html', message='No data extracted. The keyword you input cannot be found, input another keyword!'), 404
    save_extracted_data(extracted_data)
    return render_template('extract_result.html', message='Extraction process completed successfully.'), 200

def do_extraction_task_from_url(site_url):
    try:
        response = requests.get(site_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            extracted_data = []
            previous_sentence = None
            
            for paragraph in soup.find_all('p'):
                if "copyright" in paragraph.get_text(strip=True).lower() or \
                        "all rights reserved" in paragraph.get_text(strip=True).lower() or \
                        paragraph.find(class_=re.compile(r'.*\bcopyright\b.*', re.IGNORECASE)):
                    continue
                if paragraph.find_parents(class_="d-flex justify-content-between"):
                    continue
                if paragraph.find_parent(class_=re.compile(r'footer__copyright-text|footer__bottom')):
                    continue
                if paragraph.get('class') and (
                        'comment-notes' in paragraph['class'] or 'comment-form-cookies-consent' in paragraph['class']):
                    continue
                if paragraph.find_parent(class_=re.compile(r'hatnote|navigation-not-searchable')):
                    continue

                paragraph_text = str(paragraph).replace('<b>', '<b> ').replace('</b>', ' </b>').replace('<a>', '<a> ').replace('</a>', ' </a>')
                
                if is_useful_text(paragraph_text):
                    cleaned_text = clean_text(paragraph_text)
                    if cleaned_text:
                        sentences = split_sentences(cleaned_text)
                        for sentence in sentences:
                            if previous_sentence and len(previous_sentence.split()) <= 4:
                                previous_sentence += " " + sentence
                            else:
                                if previous_sentence:
                                    extracted_data.append({'url': site_url, 'sentence': previous_sentence})
                                previous_sentence = sentence

            if previous_sentence:
                extracted_data.append({'url': site_url, 'sentence': previous_sentence})
            return extracted_data
    except Exception as e:
        print(f"Error in extraction task: {str(e)}")
    return []

def clean_text_with_bold_or_link(paragraph):
    soup = BeautifulSoup(str(paragraph), 'html.parser')
    for tag in soup.find_all(['b', 'a']):
        tag.insert_after(' ')
    return soup.get_text(strip=True)

def clean_text(text):
    text = re.sub(r'\[.*?\]', '', text)
    soup = BeautifulSoup(text, 'html.parser')
    cleaned_text = soup.get_text(separator=" ", strip=True)
    cleaned_text = re.sub(r'</b>', '</b> ', cleaned_text)
    cleaned_text = re.sub(r'</a>', '</a> ', cleaned_text)
    cleaned_text = re.sub(r'[^a-zA-Z0-9\s.,;!?\'\`$]', '', cleaned_text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)

    if len(cleaned_text.strip().split()) <= 4:
        return None
    return cleaned_text.strip()

def tokenize_sentences(text):
    text = re.sub(r'[^a-zA-Z\s]', '', text).lower()
    return nltk.tokenize.sent_tokenize(text)

def split_sentences(text):
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
    return sentences

def is_useful_text(text):
    if len(text.strip()) < 3:
        return False
    if all(char in string.punctuation or char.isdigit() for char in text):
        return False
    return True
    
def analyze_sentiment(text):
    polarity_score = analyzer.polarity_scores(text)
    if polarity_score['compound'] > 0.05:
        return 'positive'
    elif polarity_score['compound'] < -0.05:
        return 'negative'
    else:
        return None

def save_extracted_data(data):
    for item in data:
        sentence = item['sentence']
        sentiment = analyze_sentiment(sentence)
        if sentiment:
            extracted_data = ExtractedData(url=item['url'], sentence=sentence, sentiment=sentiment)
            db.session.add(extracted_data)
    db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)