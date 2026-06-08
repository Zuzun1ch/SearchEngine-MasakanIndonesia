import math
import re
from collections import Counter

class BM25Model:
    def __init__(self, corpus, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.corpus = [self.tokenize(doc) for doc in corpus]
        self.doc_lens = [len(doc) for doc in self.corpus]
        self.avgdl = sum(self.doc_lens) / len(self.corpus)
        self.df = {}
        self.idf = {}
        self._calculate_df()
        self._calculate_idf()
        self.documents = corpus

    def tokenize(self, text):
        return re.findall(r'\w+', text.lower())

    def _calculate_df(self):
        for doc in self.corpus:
            for word in set(doc):
                self.df[word] = self.df.get(word, 0) + 1

    def _calculate_idf(self):
        N = len(self.corpus)
        for word, freq in self.df.items():
            self.idf[word] = math.log(1 + (N - freq + 0.5) / (freq + 0.5))

    def score(self, query, index):
        score = 0.0
        doc = self.corpus[index]
        freq = Counter(doc)
        doc_len = self.doc_lens[index]

        for word in self.tokenize(query):
            if word in freq:
                f = freq[word]
                idf = self.idf.get(word, 0)
                score += idf * (f * (self.k1 + 1)) / (f + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl))
        return score

    def search(self, query, top_n=10):
        scores = [(i, self.score(query, i)) for i in range(len(self.corpus))]
        scores.sort(key=lambda x: x[1], reverse=True)
        results = [{"rank": i+1, "index": idx, "text": self.documents[idx], "score": round(score, 4)}
                   for i, (idx, score) in enumerate(scores[:top_n])]
        return results
