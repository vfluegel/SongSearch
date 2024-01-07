from flair.data import Sentence
from flair.models import SequenceTagger
import re


# load tagger
print("Initialising NER tagger")
tagger = SequenceTagger.load("flair/ner-english-ontonotes-large")


def parse_query(query):
    # Convert query to Flair "sentence"
    sentence = Sentence(query)
    # predict NER tags
    tagger.predict(sentence)
    # print predicted NER spans
    print('The following NER tags are found:')
    # process found entities
    entities = {}
    remove_from_query = []
    for entity in sentence.get_spans('ner'):
        remove_from_query.append(entity.text)
        if entity.tag == "WORK_OF_ART":
            entities["title"] = entities.get("title", []) + [entity.text]
        elif entity.tag == "PERSON" or entity.tag == "ORG":
            entities["artist"] = entities.get("artist", []) + [entity.text]
        elif entity.tag == "DATE":
            entities["year"] = entities.get("year", []) + [parse_date(entity.text)]

        print(entity)

    tags = parse_tags(query)
    if tags:
        entities["tags"] = tags
        remove_from_query += tags

    lyrics = extract_lyrics(query, remove_from_query)
    if lyrics:
        entities["lyrics"] = lyrics
    print(entities)
    return entities


def parse_date(date_string):
    match = re.search(r"(?=the)\d{1,3}0(?=s)", date_string)
    if match:
        year_str = match.group()
        start = int(year_str if len(year_str) == 4 else f"19{year_str}")
        end = start + 9
        return {
            "type": "range",
            "start": start,
            "end": end
        }
    else:
        match = re.search(r"\d{4} - \d{4}", date_string)
        if match:
            years = match.group().split(" - ")
            start = int(years[0])
            end = int(years[1])
            return {
                "type": "range",
                "start": start,
                "end": end
            }
        else:
            match = re.search(r"\d{4}", date_string)
            if match:
                year = int(match.group())
                return {
                    "type": "exact",
                    "year": year
                }
            else:
                return None


def parse_tags(query):
    res = []
    genres = ['rap', 'rb', 'rock', 'pop', 'country']
    for genre in genres:
        if genre in query.lower():
            res.append(genre)
    return res


def extract_lyrics(query, terms_to_remove):
    query = query.lower()
    for term in terms_to_remove:
        query = query.replace(term.lower(), '')

    meta_terms = ["songs", "song", "title", "tracks", "track", "music"]
    for term in meta_terms:
        query = query.replace(term, '')

    return query.strip()
