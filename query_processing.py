import random
import spacy
from flair.data import Sentence
from flair.models import SequenceTagger
import pandas as pd
from tqdm import tqdm
from spacy.training.example import Example
from spacy.util import minibatch
from thinc.schedules import compounding
import re


def train():
    nlp = spacy.load("en_core_web_sm")
    ner = nlp.get_pipe("ner")
    examples = []
    song_data = pd.read_feather("songs_reduced.feather")
    artists = song_data['artist'].unique()
    for row in tqdm(artists, total=len(artists)):
        artist_name = row.rstrip()
        doc = nlp.make_doc(artist_name)
        example = Example.from_dict(doc, {"entities": [(0, len(artist_name), "ARTIST")]})
        examples.append(example)

    unaffected_pipes = [pipe for pipe in nlp.pipe_names if pipe != 'ner']
    ner.add_label("ARTIST")

    print("Start trainings")
    # Fine-tune the model
    optimizer = nlp.resume_training()
    with nlp.disable_pipes(*unaffected_pipes):
        for iteration in range(30):
            random.shuffle(examples)
            losses = {}
            batches = minibatch(examples, size=compounding(4.0, 32.0, 1.001))
            for batch in batches:
                nlp.rehearse(
                            batch,
                            sgd=optimizer,
                            losses=losses,
                        )
                print("Losses", losses)

    # Save the fine-tuned model
    nlp.to_disk("./model/ner_tuned")


def parse_spacy(query):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(query)
    # Extract entities and their labels
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    # Print the identified entities and their labels
    for entity, label in entities:
        print(f"Entity (spacy): {entity}, Label: {label}")


# load tagger
tagger = SequenceTagger.load("flair/ner-english-ontonotes-large")


def parse_query(query):
    # make example sentence
    sentence = Sentence(query)
    # predict NER tags
    tagger.predict(sentence)
    # print predicted NER spans
    print('The following NER tags are found:')
    # iterate over entities and print
    entities = {}
    for entity in sentence.get_spans('ner'):
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

    print(entities)
    return entities


def parse_date(date_string):
    match = re.search(r"(?!the)\d{1,3}0(?=s)", date_string)
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
