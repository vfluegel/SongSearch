import tkinter as tk
from tkinter import ttk
import csv
from whoosh.fields import Schema, TEXT
import os.path
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser

def open_database():
    with open("./song_lyrics.csv", 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        writer = ix.writer()
        i = 0
        for row in reader:
            if i <= 100:
                writer.add_document(title=row['title'], tag=row['tag'], artist=row['artist'], year=row['year'])
                i += 1
            else:
                break
        writer.commit()
        return


def search(query_str, searcher):
    query = QueryParser("title", ix.schema).parse(query_str)
    results = searcher.search(query)
    return results


def display_input():
    user_input = entry.get()

    with ix.searcher() as searcher:
        results = search(user_input, searcher)

        if results:
            result_text = "Search Results:\n"
            for result in results:
                # Access stored fields directly from the result
                result_text += f"Title: {result}\n"
        else:
            result_text = "No results found."

    result_label.config(text=result_text)


schema = Schema(title=TEXT(stored=True), tag=TEXT(stored=True), artist=TEXT(stored=True), year=TEXT(stored=True))
if not os.path.exists("index"):
    os.mkdir("index")
    create_in("index", schema)
    ix = open_dir("index")
    open_database()
else:
    ix = open_dir("index")


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

submit_button = ttk.Button(frame, text="Submit", command=display_input)
submit_button.grid(column=0, row=2, pady=(0, 10), sticky=tk.W)

result_label = ttk.Label(frame, text="")
result_label.grid(column=0, row=3, pady=(0, 10), sticky=tk.W)

app.mainloop()
