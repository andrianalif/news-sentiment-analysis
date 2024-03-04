from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

# Contoh teks berita
text = "contoh teks berita"

# Persiapkan parser teks dan tokenizer
parser = PlaintextParser.from_string(text, Tokenizer("english"))

# Buat ringkasan dengan metode LSA
summarizer = LsaSummarizer()
summary = summarizer(parser.document, sentences_count=2)  # Jumlah kalimat ringkasan yang diinginkan

# Tampilkan ringkasan
for sentence in summary:
    print(sentence)