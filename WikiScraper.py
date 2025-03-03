import re
import stanza
import nltk
import json
import requests
import time
import os
from stanza.server import CoreNLPClient
from bs4 import BeautifulSoup

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')
nltk.download('ieer')
nltk.download('conll2002')


class WikiScraper:
    """
    Scrapes text from wiki pages to be made into corpus files.

    If you leave a port open run the following
    netstat -ano | findstr :9001
    taskkill /PID  608 /f

    todo
    define function to update additonal urls
    run entirity of functions
    create kill connection
    create POS to json appender
    """

    all_text = []
    subject_sentence = {}
    object_sentence = {}
    relation_sentence = {}
    pos = {}

    def __init__(self):
        # Download the Stanford CoreNLP package with Stanza's installation command
        # This'll take several minutes, depending on the network speed
        self.document = None
        corenlp_dir = './corenlp'
        stanza.install_corenlp(dir=corenlp_dir)

        # Set the CORENLP_HOME environment variable to point to the installation location
        os.environ["CORENLP_HOME"] = corenlp_dir
        self.client = CoreNLPClient(timeout=15000, be_quiet=True,
                                    endpoint='http://localhost:9001')
        self.client.start()
        time.sleep(10)

    def scrape(self, url):
        self.page_scrape(url)
        self.generate_training_tokens()
        self.append_tokens()

    def page_scrape(self, url):
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")

        content = soup.find(id="wiki-content-block").find_all("p", attrs={'class': None})
        paragraphs = []
        for doc in content:
            if len(nltk.sent_tokenize(doc.getText())) > 1:
                paragraphs.append(nltk.sent_tokenize(doc.getText()))

        for paragraph in paragraphs:
            for sentence in paragraph:
                self.all_text.append(sentence)

    # needs modified still
    def get_relationships(self):
        tokenized_sentences = [nltk.sent_tokenize(sentence) for sentence in self.all_text]
        tokenized_word = [nltk.word_tokenize(sentence) for sentence in self.all_text]
        tagged_sentences = [nltk.pos_tag(sentence) for sentence in tokenized_word]
        chunked_sentences = [nltk.ne_chunk(sentence) for sentence in tagged_sentences]
        print("token word")
        for s in tokenized_word:
            print(s)
        print("token sent")
        for s in tokenized_sentences:
            print(s)
        print("Tag")
        for s in tagged_sentences:
            print(s)
        print("chunk")
        for s in chunked_sentences:
            print(s)
        IS = re.compile(r'.*\bis\b(?!\b.+ing)')
        for i in range(len(chunked_sentences)):
            for rel in nltk.sem.extract_rels('PERSON', 'ORGANIZATION', chunked_sentences[i], corpus='ace', pattern=IS):
                print(self.all_text[i])
        return self.space_swap(tokenized_sentences)  # this will need changed

    # Setters
    def generate_training_tokens(self):
        postags = ['NNPS', 'NNP']
        for text in self.all_text:
            self.document = self.client.annotate(text, annotators='pos', output_format='json')
            for sentence in self.document['sentences']:
                for token in sentence['tokens']:
                    if (token['pos'] in postags) or (token['index'] == 1 and 'NN' in token['pos']):
                        self.pos.append({"topic": token['word'], "inputs": [token['word']], "responses": [text]})

    def append_tokens(self):
        with open('training_data/training.json', 'r+') as file:
            file_data = json.load(file)
            file_data["topics"].append(self.pos)
            file.seek(0)
            json.dump(file_data, file, indent=4)

    # Getters
    def get_toke_sent(self):
        tokenized_sentences = [nltk.sent_tokenize(sentence) for sentence in self.all_text]
        return self.space_swap(tokenized_sentences)

    def get_all_text(self):
        return self.all_text

    def get_triplets(self):
        triples = []
        for text in self.all_text:
            self.document = self.client.annotate(text, annotators='openie', output_format='json')
            for sentence in self.document['sentences']:
                for triple in sentence['openie']:
                    print(sentence)
                    triples.append({
                        'subject': triple['subject'],
                        'relation': triple['relation'],
                        'object': triple['object']
                    })
                    self.subject_sentence.append({triple['subject']: text})
                    self.relation_sentence.append({triple['relation']: text})
                    self.object_sentence.append({triple['object']: text})
        return triples

    def get_subject_sentence(self):
        return self.subject_sentence

    def get_relation_sentence(self):
        return self.relation_sentence

    def get_object_sentence(self):
        return self.object_sentence

    def get_tokenized_nouns(self):
        return self.pos

    # needs modified still
    def get_relationships(self):
        tokenized_sentences = [nltk.sent_tokenize(sentence) for sentence in self.all_text]
        tokenized_word = [nltk.word_tokenize(sentence) for sentence in self.all_text]
        tagged_sentences = [nltk.pos_tag(sentence) for sentence in tokenized_word]
        chunked_sentences = [nltk.ne_chunk(sentence) for sentence in tagged_sentences]
        print("token word")
        for s in tokenized_word:
            print(s)
        print("token sent")
        for s in tokenized_sentences:
            print(s)
        print("Tag")
        for s in tagged_sentences:
            print(s)
        print("chunk")
        for s in chunked_sentences:
            print(s)
        IS = re.compile(r'.*\bis\b(?!\b.+ing)')
        for i in range(len(chunked_sentences)):
            for rel in nltk.sem.extract_rels('PERSON', 'ORGANIZATION', chunked_sentences[i], corpus='ace', pattern=IS):
                print(self.all_text[i])
        return self.space_swap(tokenized_sentences)  # this will need changed

    # Utility methods
    def space_swap(self, lst):
        text_mod = []
        for s in lst:
            text_mod.append(str(s).replace(u'\xa0', u' '))
        return text_mod

    def stop_client(self):
        self.client.stop()
