import lucene
import os
import pandas as pd
from java.nio.file import Paths
from tqdm import tqdm
from org.apache.lucene.analysis.miscellaneous import LimitTokenCountAnalyzer
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import Document, Field, StringField, TextField, IntPoint
from org.apache.lucene.index import FieldInfo, IndexWriter, DirectoryReader, IndexWriterConfig, IndexOptions, Term
from org.apache.lucene.store import FSDirectory, NIOFSDirectory
from org.apache.lucene.search import IndexSearcher, TermQuery, BoostQuery, BooleanQuery, BooleanClause, ScoreDoc, \
    TopDocs
from org.apache.lucene.queryparser.classic import QueryParser

lucene.initVM()
print(f"Lucene: {lucene.VERSION}")


def create_index(index_dir):
    if not os.path.exists(index_dir):
        os.mkdir(index_dir)

    analyzer = StandardAnalyzer()
    config = IndexWriterConfig(analyzer)
    directory = FSDirectory.open(Paths.get(index_dir))
    writer = IndexWriter(directory, config)

    print("Reading file...")
    songs = pd.read_feather("./songs_filtered.feather")
    print("Generating index...")
    for row in tqdm(songs.itertuples(), total=songs.shape[0]):
        doc = Document()
        if None in row:
            continue
        doc.add(TextField("title", row.title, Field.Store.YES))
        doc.add(StringField("tag", row.tag, Field.Store.NO))
        doc.add(StringField("artist", row.artist, Field.Store.YES))
        doc.add(IntPoint("year", row.year))
        doc.add(TextField("lyrics", row.lyrics, Field.Store.NO))
        writer.addDocument(doc)

    writer.close()


def get_searcher(index_dir):
    directory = FSDirectory.open(Paths.get(index_dir))
    reader = DirectoryReader.open(directory)
    return IndexSearcher(reader)


def search_index(searcher, query):
    final_query = BooleanQuery.Builder()

    for artist in query.get("artist", []):
        artist_term = Term("artist", artist)
        q_artist = TermQuery(artist_term)
        final_query.add(BoostQuery(q_artist, 2.0), BooleanClause.Occur.SHOULD)

    for year in query.get("year", []):
        if year["type"] == "range":
            q_year = IntPoint.newRangeQuery("year", year["start"], year["end"])
        elif year["type"] == "exact":
            q_year = IntPoint.newExactQuery("year", year["year"])
        else:
            raise NotImplemented("Date format not supported")
        final_query.add(BoostQuery(q_year, 2.0), BooleanClause.Occur.SHOULD)

    for tag in query.get("tags", []):
        tag_term = Term("tag", tag)
        q_tag = TermQuery(tag_term)
        final_query.add(BoostQuery(q_tag, 2.0), BooleanClause.Occur.MUST)

    for title in query.get("title", []):
        query_parser = QueryParser("title", StandardAnalyzer())
        q_title = query_parser.parse(title)
        final_query.add(q_title, BooleanClause.Occur.SHOULD)

    combined_query = BooleanQuery.Builder()
    combined_query.add(final_query.build(), BooleanClause.Occur.MUST)
    if query.get("lyrics"):
        lyrics_parser = QueryParser("lyrics", StandardAnalyzer())
        q_lyrics = lyrics_parser.parse(query['lyrics'])
        combined_query.add(q_lyrics, BooleanClause.Occur.SHOULD)

    top_docs = searcher.search(combined_query.build(), 20)
    score_docs = top_docs.scoreDocs

    for score_doc in score_docs:
        doc_id = score_doc.doc
        doc = searcher.doc(doc_id)
        print(f"Content: {doc.get('title')} ({doc.get('artist')})")

    return [searcher.doc(res.doc) for res in score_docs]


# EXAMPLE CODE
def test():
    create_index("./lucene_index")

    index_searcher = get_searcher(":/lucene_index")
    print("Initial results")
    results = search_index(index_searcher, {"title": ["new year"], "artist": ["Taylor Swift"],
                                            "year": [{"type": "range", "start": 2010, "end": 2019}],
                                            "lyrics": "glitter on the floor"})
