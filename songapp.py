import tkinter as tk
from tkinter import ttk
import csv
from tqdm import tqdm
from whoosh.fields import Schema, TEXT, KEYWORD
from whoosh import scoring, qparser
from whoosh.fields import Schema, TEXT, NUMERIC
import os.path
from whoosh.index import create_in, open_dir
from whoosh.qparser import MultifieldParser, QueryParser
import shutil
import pandas

user_feedback = {}


def open_database():
    print("Open data file...")
    songs = pandas.read_feather("./songs_filtered.feather")
    writer = ix.writer(limitmb=2048)

    print("Generating index...")
    for row in tqdm(songs.itertuples(), total=songs.shape[0]):
        writer.add_document(title=row.title, tag=row.tag, artist=row.artist, year=row.year, lyrics=row.lyrics)

    writer.commit()
    print("Index finished!")


def search(query_str, searcher, search_fields, schema):
    or_group = qparser.OrGroup.factory(0.9)
    mparser = MultifieldParser(search_fields, schema, group=or_group)
    query = mparser.parse(query_str)
    results = searcher.search(query, limit=100)
    return results

'''
 Here is the button command, where we could implement a feedback logic ( if possible)
'''
def remove_result(result,scores):
    # Define the logic to remove the result
    print(f"Remove the result: {result['title']} | Artist: {result['artist']}")
    user_feedback[result['title']] = result['artist']
    result_label.config(text="")
    #display_input()

'''
 Second Selection, After the first one selected the songs that belongs to the proper artist/years 
 We now use the TF-IDF to score the remaining songs only looking at their lyrics, using the temporary schema
'''
def second_query(user_input, docs, custom_schema=None):
    search_fields = ["lyrics"]

    result_label.config(text="Generating your playlist....")
    with ix.searcher(weighting=scoring.TF_IDF()) as searcher:
        or_group = qparser.OrGroup
        mparser = QueryParser("lyrics", ix.schema, group=or_group)
        query = mparser.parse(user_input)
        results = searcher.search(query, limit=30, filter=docs)
        #results = search(user_input, searcher, search_fields, schema)

        if results:
            display_results(results)
        else:
            result_text = "No results found (2)."


def display_results(results):
    result_text = ""
    # save the scores for the documents ( might need for a feedback retrieval??)
    scores_dict = {(result['title'], result['artist']): result.score for result in results}

    for i, result in enumerate(results):
        # print
        result_text += f"{result['title']} | Artist: {result['artist']} | Score: {result.score:.4f}\n"

        # button for the feedback, style sucks I am horrible at design but I didn't want to waste time on moving buttons
        # plus they don't disappear with sequential queries so they stack. Just don't look to the right while running the app
        remove_button = ttk.Button(frame,
                                   text=f"{result['title']} | Artist: {result['artist']}",
                                   command=lambda r=result: remove_result(r, scores_dict))
        remove_button.grid(row=i, column=1, sticky=tk.W, padx=(5, 0))
        if i >= 9:
            # Here I retrieved 100 items but only want to print out 10.
            # I retrieved 100 to save the scores and use them to fix the list after a feedback, so it's faster
            # IMPORTANT!!! feedback is just an idea rn and it's not implemented, so everything related to that is
            # just a scratch
            break

    result_label.config(text=result_text)

'''
 First Selection, Must be changed so that it uses a "binary like" logic on dates, artists and tags. 
 Right now it uses BM25F (default) 
'''
def first_query():

    result_label.config(text="Getting the songs...")
    user_input = entry.get()
    search_fields = ["title", "tag", "artist", "year"]

    with ix.searcher() as searcher:
        results = search(user_input, searcher, search_fields, ix.schema)
        use_second = False
        if use_second:
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
            second_query(user_input, tmp_ix.schema)
        elif results:
            second_query(user_input, {res.docnum for res in results})
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
tmp_schema = Schema(title=TEXT(stored=True), tag=KEYWORD, artist=TEXT(stored=True), year=NUMERIC(stored=True),
                    lyrics=TEXT(vector=True))

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
