import tkinter as tk
from tkinter import ttk
import os.path
import lucene_searcher
from query_processing import parse_query


def submit_query():
    """Convert the user NL input to a Lucene query and start search"""
    user_input = entry.get()

    query_dict = parse_query(user_input)
    lucene_query = lucene_searcher.build_query(query_dict)
    search_and_display(lucene_query)


def search_and_display(query):
    """Perform actual search in Lucene and add results to UI"""
    # Remove former results
    for widget in result_frame.winfo_children():
        widget.destroy()

    results = lucene_searcher.perform_search(index_searcher, query)
    if results:
        print("Query done...")
        for i, result in enumerate(results):
            # Insert song name and button to like the song
            result_label = ttk.Label(result_frame,
                                     text=f"{result['song']['title']} | Artist: {result['song']['artist']} ({result['song']['year_value']})")
            result_label.grid(row=i, column=0, padx=(2, 4), sticky="w")
            like_button = ttk.Button(result_frame, text="I Like!",
                       command=lambda song=result: like_result(song, query))
            like_button.grid(row=i, column=1, pady=1)
    else:
        # Display message if no results are found
        result_label = ttk.Label(result_frame, text="No results found")
        result_label.pack()


def like_result(song, original_query):
    """Mark a song as good result and expand the query accordingly"""
    updated_query = lucene_searcher.expand_query(index_reader, original_query, song)
    search_and_display(updated_query)


'''
Initialise the Lucene searcher
'''
index_dir = "./lucene_index"
if not os.path.exists(index_dir):
    lucene_searcher.create_index("./lucene_index")
index_reader, index_searcher = lucene_searcher.get_reader_and_searcher(index_dir)


'''
PANEL and STYLE
'''
# Main App
app = tk.Tk()
app.title("Song App")
app.columnconfigure(0, weight=1)

style = ttk.Style()
style.theme_use("default")

# Frame for content
frame = ttk.Frame(app, padding=(10, 10, 10, 10))
frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# Frame for the search form and content
search_frame = ttk.Frame(frame)
search_frame.grid(column=0, row=0, pady=5)
prompt_label = ttk.Label(search_frame, text="Enter a prompt:")
prompt_label.grid(column=0, row=0, pady=(0, 5), sticky=tk.W)

entry = ttk.Entry(search_frame, width=60)
entry.grid(column=0, row=1, pady=(0, 10), sticky=tk.W)

submit_button = ttk.Button(search_frame, text="Submit", command=submit_query)
submit_button.grid(column=0, row=2, pady=(0, 10), sticky=tk.W)

# Frame to display the results
result_frame = ttk.Frame(frame)
result_frame.columnconfigure(0, weight=1)
result_frame.grid(column=0, row=1, sticky="w")

app.mainloop()
