let globalKeywords = [];

function showTopWords() {
    const text = document.getElementById('news-content').innerText;
    const wordCounts = {};
    const words = text.replace(/[0-9\.,-\/#!$%\^&\*;:{}=\-_`~()]/g,"")
                .toLowerCase()
                .split(/\s+/);
    const unwantedWords = new Set([
        /*bahasa indonesia*/
        "yang", "untuk", "pada", "ke", "para", "namun", "menurut", "antara", "dia", "dua", "ia", "seperti", "jika", "sehingga", "kembali", "dan", "tidak", "ini", "karena", "kepada", "oleh", "saat", "harus", "sementara", "setelah", "belum", "kami", "sekitar", "bagi", "serta di", "dari", "telah", "sebagai", "masih", "hal", "ketika", "adalah", "itu", "dalam", "bisa", "bahwa", "atau", "hanya", "rp",
        "ini", "ada", "pt", "pama", "pamapersada nusantara", "pamapersada", "nusantara", "tahun", "batu", "bara", "wib", "kita", "dengan", "juga", "akan", "ada", "wib", "wita", "wit", "mereka", "sudah", "saya", "terhadap", "secara", "agar", "lain", "anda", "begitu", "mengapa", "kenapa", "yaitu", "yakni", "daripada", "itulah", "lagi", "maka", "tentang", "demi", "dimana", "kemana", "pula", "sambil", "sebelum", "berita", "sesudah", "supaya", "guna", "kah", "pun", "sampai", "sedangkan", "selagi", "seolah", "seraya", "seterusnya", "tanpa", "agak", "boleh", "dapat", "dsb", "dst", "dll", "dahulu", "dulunya", "demikian", "tapi", "ingin", "juga", "tidak", "mari", "nanti", "melainkan", "oh", "ok", "seharusnya", "sebetulnya", "setiap", "setidaknya", "sesuatu", "pasti", "saja", "ya", "walau", "tolong", "tentu", "amat", "apalagi", "bagaimanapun", "dengan", "ia", "bahwa", "di", "t", "cnbc", "kompas", "kilas", "cara", "indonesia",

        /*bahasa inggris*/
        "which", "for", "at", "to", "the", "however", "according to", "between", "he", "two", "he", "like", "if", "so", "back", "and", "not", "this", "because", "to", "by", "when", "should", "while", "after", "yet", "we", "about", "for", "as well as in", "of", "has", "as", "still", "thing", "when", "is", "that", "in", "could", "that", "or", "only", "rp", "this", "there", "pt", "pama", "pamapersada nusantara", "nusantara", "year", "stone", "bara", "whats", "we", "with", "also", "will", "there", "them", "already", "me", "against", "in", "in order", "other", "you", "so", "why", "why", "that", "namely", "than", "that", "again", "then", "about", "for", "where", "where", "anyway", "while", "before", "after", "so that", "in order to", "is", "pun", "until", "while", "while", "as if", "while", "so on", "without", "rather", "may", "can", "etc", "was", "was", "so", "but", "want", "also", "not", "let's", "later", "but", "oh", "ok", "should", "actually", "every", "at least", "something", "definitely", "only", "yes", "although", "please", "certainly", "very", "moreover", "however", "with", "it", "that", "at", "new", "food", "news"
    ]);

    for (const word of words) {
        if (word && !unwantedWords.has(word)) {
            wordCounts[word] = (wordCounts[word] || 0) + 1;
        }
    }

    const topFiveWords = Object.entries(wordCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(entry => entry[0]);
    const strongElement = document.createElement('strong');
    strongElement.innerText = 'Keywords: ' + topFiveWords.join(', ');
    strongElement.style.paddingBottom = '10px';
    
    globalKeywords = topFiveWords;
    
    let urlElement = document.getElementById('url');

    if (urlElement) {
        let url = urlElement.value;
        let data = {
            url: url,
            keywords: globalKeywords
        };
    }
    
    fetch('/save_keywords', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ keywords: globalKeywords })
    });
    
    const topWordsElement = document.getElementById('top-words');
    topWordsElement.innerHTML = '';
    topWordsElement.appendChild(strongElement);
}

function downloadCSV(csvContent, fileName) {
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = fileName;
    link.click();
}

function downloadActivitiesCSV() {
    window.open('/download_activities_csv', '_blank');
}       

function goBack() {
    window.history.back();
}