import tkinter as tk
from tkinter import ttk
import csv
from whoosh import scoring
from whoosh.fields import Schema, TEXT
import os.path
from whoosh.index import create_in, open_dir
from whoosh.qparser import MultifieldParser
import nltk
from nltk.corpus import wordnet
import shutil

nltk.download('wordnet')
user_feedback = {}

def open_database():
    with open("./song_lyrics.csv", 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        writer = ix.writer()
        i = 0
        for row in reader:
            if i <= 100:
                writer.add_document(title=row['title'], tag=row['tag'], artist=row['artist'], year=row['year'], lyrics=row['lyrics'])
                i += 1
            else:
                break
        writer.commit()


def search(query_str, searcher, search_fields, schema):
    mparser = MultifieldParser(search_fields, schema)
    query = mparser.parse(query_str)
    results = searcher.search(query, limit=100)
    return results

'''
 Here is the button command, where we could implement a feedback logic ( if possible)
'''
def remove_result(user_input, result, synonymous, schema):
    # Define the logic to remove the result
    print(f"Remove the result: {result['title']} | Artist: {result['artist']}")
    user_feedback[result['title']] = result['artist']
    result_label.config(text="")
    for list in synonymous:
        for term in list:
            user_input += f" OR {term}"
    print(user_input)
    second_query(user_input, schema)

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
def second_query(user_input, schema):
    search_fields = ["lyrics"]

    with ix.searcher(weighting=scoring.TF_IDF()) as searcher:
        results = search(user_input, searcher, search_fields, schema)

        if results:
            result_text = ""

            for i, result in enumerate(results):
                # print
                result_text += f"{result['title']} | Artist: {result['artist']} | Score: {result.score:.4f}\n"

                # gets most frequent terms
                doc_id = result.docnum
                term_vector = searcher.reader().vector(doc_id, "lyrics")
                field_length = searcher.reader().doc_field_length(doc_id, "lyrics")
                terms = term_vector.items_as("frequency")
                sorted_terms = sorted(terms, key=lambda x: x[1], reverse=True)

                # gets synonyms
                synonymous = []
                for term, freq in sorted_terms[:5]:
                    synonym = get_synonyms(term)
                    if synonym:
                        synonymous.append(synonym)
                    else:
                        print(f"No synonyms found for {term}")

                '''
                print(f"result: {result['title']} | Artist: {result['artist']}")
                print(f"Most frequent terms [{field_length}]:")
                for term, freq in sorted_terms[:5]:
                    print(f"{term}: {freq} times")

                keywords = [keyword for keyword, score
                            in results.key_terms("lyrics", docs=10, numterms=20)]
                print(f"keywords[{keywords}]:")
                '''


                # button for the feedback, style sucks I am horrible at design but I didn't want to waste time on moving buttons
                # plus they don't disappear with sequential queries so they stack. Just don't look to the right while running the app
                remove_button = ttk.Button(frame,
                                           text=f"{result['title']} | Artist: {result['artist']}",
                                           command=lambda r=result: remove_result(user_input, r, synonymous, schema))
                remove_button.grid(row=i, column=1, sticky=tk.W, padx=(5, 0))
                if i >= 9:
                    #Here I retrieved 100 items but only want to print out 10.
                    #I retrieved 100 to save the scores and use them to fix the list after a feedback, so it's faster
                    #IMPORTANT!!! feedback is just an idea rn and it's not implemented, so everything related to that is
                    #just a scratch
                    break
        else:
            result_text = "No results found (2)."

    result_label.config(text=result_text)

'''
 First Selection, Must be changed so that it uses a "binary like" logic on dates, artists and tags. 
 Right now it uses BM25F (default) 
'''
def first_query():
    user_input = entry.get()
    search_fields = ["title", "tag", "artist", "year", "lyrics"]

    with ix.searcher() as searcher:
        results = search(user_input, searcher, search_fields, ix.schema)
        if results:
            # make a new temporary schema for the new query
            if os.path.exists("tmp_index"):
                shutil.rmtree("tmp_index")
            os.mkdir("tmp_index")
            create_in("tmp_index", tmp_schema)
            tmp_ix = open_dir("tmp_index")
            tmp_writer = tmp_ix.writer()
            for result in results:
                tmp_writer.add_document(title=result['title'], tag=result['tag'], artist=result['artist'], year=result['year'], lyrics=result['lyrics'])
            # run the second query
            tmp_writer.commit()
            second_query(user_input, tmp_ix.schema)
        else:
            result_text = "No results found (1)."
            result_label.config(text=result_text)
    return

'''
First schema, with all the songs
'''
schema = Schema(title=TEXT(stored=True), tag=TEXT(stored=True), artist=TEXT(stored=True), year=TEXT(stored=True), lyrics=TEXT(stored=True, vector=True))
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
tmp_schema = Schema(title=TEXT(stored=True), tag=TEXT(stored=True), artist=TEXT(stored=True), year=TEXT(stored=True), lyrics=TEXT(stored=True, vector=True))

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
