from flask import Flask, render_template, request
import pandas as pd
from bm25 import BM25Model

app = Flask(__name__)

# ======================
# LOAD DATASET
# ======================
data = pd.read_csv('cookpad_recipes.csv')

# ======================
# HANDLE NULL VALUE
# ======================
data = data.fillna("")

# ======================
# TITLE BOOSTING
# Judul diulang 5x agar lebih relevan
# ======================
documents = (
    (data['Title'].astype(str) + " ") * 5 +
    data['Ingredients'].astype(str)
).tolist()

# ======================
# INIT BM25
# ======================
bm25 = BM25Model(documents)

# ======================
# HOME
# ======================
@app.route('/')
def index():
    return render_template('index.html')

# ======================
# SEARCH
# ======================
@app.route('/search', methods=['POST'])
def search():

    query = request.form['query'].lower()

    # ======================
    # SEARCH BM25
    # ======================
    raw_results = bm25.search(query)

    # ======================
    # FILTER RELEVAN
    # Query harus muncul di title
    # ======================
    filtered_results = []

    for result in raw_results:

        idx = result['index']
        row = data.iloc[idx]

        title = str(row['Title']).lower()

        # hanya ambil title yg relevan
        if query in title:

            filtered_results.append(result)

    # ======================
    # FORMAT OUTPUT
    # ======================
    results = []

    for result in filtered_results:

        idx = result['index']
        row = data.iloc[idx]

        results.append({

            "rank": result["rank"],

            "score": round(result["score"], 4),

            "title": row['Title'],

            "ingredients": row['Ingredients'],

            "author": row['Author'],

            "steps": row['Steps'],

            "servings": row['Servings'],

            "url": row['Link']

        })

    return render_template(
        "result.html",
        query=query,
        results=results
    )

# ======================
# RUN FLASK
# ======================
if __name__ == '__main__':
    app.run(debug=True)