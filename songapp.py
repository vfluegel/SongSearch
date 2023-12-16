import tkinter as tk
from tkinter import ttk
import pandas
from tqdm import tqdm
from whoosh import scoring, qparser
from whoosh.fields import Schema, TEXT, KEYWORD, NUMERIC
import csv
import os.path
from whoosh.index import create_in, open_dir
from whoosh.qparser import MultifieldParser
import nltk
from nltk.corpus import wordnet

nltk.download('wordnet')
remove_buttons = []
current_words = []


def open_database():
    print("Open data file...")
    songs = pandas.read_feather("./songs_filtered.feather")
    writer = ix.writer(limitmb=2048)

    print("Generating index...")
    i = 0
    j = 1
    for row in tqdm(songs.itertuples(), total=songs.shape[0]):
        i += 1
        try:
            writer.add_document(title=row.title, tag=row.tag, artist=row.artist, year=row.year, lyrics=row.lyrics)
        except Exception as e:
            print(f"Skipping {row.title} by {row.artist}")
            print(f"An exception occurred: {e}")
        if i >= 10000:
            writer.commit()
            writer = ix.writer(limitmb=2048)
            print(f"Index finished! {j}")
            j += 1
            i = 0

    writer.commit()
    print("Index finished!")


def search(query_str, searcher, search_fields, schema, docnums = None):
    or_group = qparser.OrGroup.factory(0.9)
    mparser = MultifieldParser(search_fields, schema, group=or_group)
    query = mparser.parse(query_str)
    if docnums is not None:
        results = searcher.search(query, limit=100, filter=docnums)
    else:
        results = searcher.search(query, limit=100)
    return results

'''
 Here is the button command, where we could implement a feedback logic ( if possible)
'''
def remove_result(user_input, result, synonymous, docnums):
    global current_words
    # Define the logic to remove the result
    print(f"Remove the result: {result['title']} | Artist: {result['artist']}")
    result_label.config(text="")
    for list_t in synonymous:
        for term in list_t:
            term = term.replace('_', ' ')
            if ' ' in term:
                term = f"\"{term}\""
            if term not in current_words:
                user_input += f" OR {term}"
                current_words.append(term)
    print(user_input)
    second_query(user_input, docnums)

def get_synonyms(word):
    synonyms = []

    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.append(lemma.name())

    return set(synonyms)

'''
 Second Selection, After the first one selected the songs that belongs to the proper artist/years 
 We now use the TF-IDF to score the remaining songs only looking at their lyrics, using the temporary schema
'''
def second_query(user_input, docnums):
    global remove_buttons
    global current_words
    search_fields = ["lyrics"]
    with ix.searcher(weighting=scoring.TF_IDF()) as searcher:
        results = search(user_input, searcher, search_fields, ix.schema, docnums)

        if results:
            result_text = ""
            for button in remove_buttons:
                button.destroy()

            remove_buttons = []

            for i, result in enumerate(results):
                # print
                result_text += f"{result['title']} | Artist: {result['artist']} | Score: {result.score:.4f}\n"

                # gets most frequent terms
                doc_id = result.docnum
                term_vector = searcher.reader().vector(doc_id, "lyrics")
                terms = term_vector.items_as("frequency")
                sorted_terms = sorted(terms, key=lambda x: x[1], reverse=True)

                # gets synonyms
                synonymous = []
                for term, freq in sorted_terms[:5]:
                    synonym = get_synonyms(term)
                    if synonym:
                        synonymous.append(synonym)

                remove_button = ttk.Button(frame,
                                           text=f"{result['title']} | Artist: {result['artist']}",
                                           command=lambda r=result, s=synonymous : remove_result(user_input, r, s, docnums))
                remove_button.grid(row=i, column=1, sticky=tk.W, padx=(5, 0))

                remove_buttons.append(remove_button)

                if i >= 9:
                    break
        else:
            result_text = "No results found (2)."

    result_label.config(text=result_text)

'''
 First Selection, Must be changed so that it uses a "binary like" logic on dates, artists and tags. 
 Right now it uses BM25F (default) 
'''
def first_query():
    global current_words
    current_words = []
    user_input = entry.get()
    words = user_input.split()
    for word in words:
        current_words.append(word)
    search_fields = ["title", "tag", "artist", "year", "lyrics"]

    with ix.searcher() as searcher:
        results = search(user_input, searcher, search_fields, ix.schema)
        if results:
            print("first query done...")
            # run the second query
            second_query(user_input, results)
        else:
            result_text = "No results found (1)."
            result_label.config(text=result_text)
    return

'''
First schema, with all the songs
'''
schema = Schema(title=TEXT(stored=True), tag=KEYWORD, artist=TEXT(stored=True), year=NUMERIC(stored=True),
                lyrics=TEXT(vector=True))
if not os.path.exists("index"):
    os.mkdir("index")
    create_in("index", schema)
    ix = open_dir("index")
    open_database()
else:
    ix = open_dir("index")

'''
Second schema, that is emptied each time. 
Here we save only the songs that survive to the first scan ( aka binary search ) 
and so we scan this schema for the TF-IDF algo
'''
tmp_schema = Schema(title=TEXT(stored=True), tag=TEXT(stored=True), artist=TEXT(stored=True), year=NUMERIC(stored=True), lyrics=TEXT(stored=True))

'''
PANEL and STYLE
'''
app = tk.Tk()
app.title("Song App")

style = ttk.Style()
style.theme_use("default")

frame = ttk.Frame(app, padding=(10, 10, 10, 10))
frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

prompt_label = ttk.Label(frame, text="Enter a prompt:")
prompt_label.grid(column=0, row=0, pady=(0, 5), sticky=tk.W)

entry = ttk.Entry(frame, width=60)
entry.grid(column=0, row=1, pady=(0, 10), sticky=tk.W)

submit_button = ttk.Button(frame, text="Submit", command=first_query)
submit_button.grid(column=0, row=2, pady=(0, 10), sticky=tk.W)

result_label = ttk.Label(frame, text="")
result_label.grid(column=0, row=3, pady=(0, 10), sticky=tk.W)

app.mainloop()
