import os.path
import lucene_searcher
from query_processing import parse_query

def submit_query():
    """Convert the user NL input to a Lucene query and start search"""
    user_input = input("Enter a prompt: ")
    query_dict = parse_query(user_input)
    lucene_query = lucene_searcher.build_query(query_dict)
    search_and_display(lucene_query)

def search_and_display(query):
    """Perform actual search in Lucene and print results"""
    results = lucene_searcher.perform_search(index_searcher, query)
    if results:
        print("Query done...")
        for i, result in enumerate(results):
            print(f"{result['song']['title']} | Artist: {result['song']['artist']} ({result['song']['year_value']})")
    else:
        print("No results found")

def like_result(song, original_query):
    """Mark a song as a good result and expand the query accordingly"""
    updated_query = lucene_searcher.expand_query(index_reader, original_query, song)
    search_and_display(updated_query)

'''
Initialise the Lucene searcher
'''
index_dir = "./lucene_index"
if not os.path.exists(index_dir):
    lucene_searcher.create_index("./lucene_index")
index_reader, index_searcher = lucene_searcher.get_reader_and_searcher(index_dir)

# Main loop for command-line interface
while True:
    submit_query()
    user_response = input("Do you want to continue searching? (yes/no): ").lower()
    if user_response != 'yes':
        break
