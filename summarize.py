from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

# Contoh teks berita
text = "several killed in chad after attack on intelligence agency foiled, government says | cnn cnn values your feedback 1. how relevant is this ad to you? 2. did you encounter any technical issues? video player was slow to load content video content never loaded ad froze or did not finish loading video content did not start after ad audio on ad was too loud other issues ad never loaded ad prevented/slowed the page from loading content moved around while ad loaded ad was repetitive to ads i've seen previously other issues cancel submit thank you! your effort and contribution in providing this feedback is much                                         appreciated. close  close icon world africa americas asia australia china europe india middle east united kingdom more africa americas asia australia china europe india middle east united kingdom watch audio live tv log in my account settings topics you follow log out your cnn account log in to your cnn account search log in my account settings topics you follow log out your cnn account log in to your cnn account live tv audio watch edition us international arabic español edition us international arabic español africa americas asia australia china europe india middle east united kingdom follow cnn world africa americas asia australia china europe india middle east united kingdom us politics scotus congress facts first 2024 elections business tech media calculators videos markets pre-markets after-hours market movers fear & greed world markets investing markets now before the bell nightcap health life, but better fitness food sleep mindfulness relationships entertainment movies television celebrity tech innovate gadget foreseeable future mission: ahead upstarts work transformed innovative cities style arts design fashion architecture luxury beauty video travel destinations food & drink stay news videos sports football tennis golf motorsport us sports olympics climbing esports hockey watch live tv digital studios cnn films hln tv schedule tv shows a-z cnnvr features as equals call to earth freedom project impact your world inside africa 2 degrees cnn heroes all features weather climate wildfire tracker video more photos longform investigations cnn profiles cnn leadership cnn newsletters work for cnn  several killed in chad after attack on intelligence agency foiled, government says by niamh kennedy and bethlehem feleke , cnn 2 minute read published         4:57 pm est, wed february 28, 2024 link copied! follow: national security see all topics cnn nairobi cnn — tensions were high in the central african country of chad on wednesday after several people were killed following an alleged attack on the country’s intelligence services was foiled overnight, the government said. the country’s communications ministry said the situation took “a dramatic turn” after a “deliberate attack” was allegedly carried out by members of the opposition socialist party without borders (psf) on the headquarters of the country’s national state security agency (anse) in the capital n’djamena. cnn has reached out to the leader of the party, yaya dillo, about the accusations. dillo said in a facebook post on wednesday morning that the military had surrounded him and others at the party’s headquarters. law enforcement officers managed to foil the attack “with efficiency,” the ministry said, claiming that the situation was now “completely under control.” the government also accused the finance secretary of the opposition party for being behind an assassination attempt against the president of the supreme court on wednesday. it’s not clear if it was a separate incident or the court president was in the security agency’s office during the attack. the tensions come as chad gears up for presidential elections in may which will mark the first of their kind since military leader general mahamat idriss deby took over in 2020 after his father was killed on the battlefield. “it is important to highlight that every person searching to disrupt the democratic process underway in the country will be taken to court,” the government warned. no details on the total number of casualties from the attack were provided in the statement with the authorities promising to release the death toll “later on.” internet monitoring firm, netblocks said shortly after 7aet its network data showed there had been a “disruption to internet connectivity” in the country following the reports of a “deadly attack” on the intelligence agency headquarters.      search log in my account settings topics you follow log out your cnn account log in to your cnn account live tv listen watch world africa americas asia australia china europe india middle east united kingdom us politics scotus congress facts first 2024 elections business markets tech media calculators videos health life, but better fitness food sleep mindfulness relationships entertainment movies television celebrity tech innovate gadget foreseeable future mission: ahead upstarts work transformed innovative cities style arts design fashion architecture luxury beauty video travel destinations food & drink stay news videos sports football tennis golf motorsport us sports olympics climbing esports hockey watch live tv digital studios cnn films hln tv schedule tv shows a-z cnnvr features as equals call to earth freedom project impact your world inside africa 2 degrees cnn heroes all features weather climate wildfire tracker video more photos longform investigations cnn profiles cnn leadership cnn newsletters work for cnn world watch listen live tv follow cnn log in my account settings topics you follow log out your cnn account log in to your cnn account terms of use privacy policy ad choices accessibility & cc about newsletters transcripts © 2024 cable news network. a warner bros. discovery company. . cnn sans ™ & © 2016 cable news network."

# Persiapkan parser teks dan tokenizer
parser = PlaintextParser.from_string(text, Tokenizer("english"))

# Buat ringkasan dengan metode LSA
summarizer = LsaSummarizer()
summary = summarizer(parser.document, sentences_count=2)  # Jumlah kalimat ringkasan yang diinginkan

# Tampilkan ringkasan
for sentence in summary:
    print(sentence)