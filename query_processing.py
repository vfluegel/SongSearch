import spacy
import pandas as pd
from spacy.training.example import Example


nlp = spacy.load("en_core_web_sm")
ner = nlp.get_pipe("ner")
ner.add_label("ARTIST")

examples = []
song_data = pd.read_feather("songs_reduced.feather")
for index, row in song_data.iterrows():
    artist_name = row['artist'].rstrip()
    doc = nlp.make_doc(artist_name)
    example = Example. from_dict(doc, {"entities": [(0, len(artist_name), "ARTIST")]})
    examples.append(example)

print("Start trainings")
# Fine-tune the model
optimizer = nlp.create_optimizer()
for epoch in range(10):
    print(f"New round {epoch}...")
    for example in examples:
        optimizer.update([example], drop=0.5)

# Save the fine-tuned model
optimizer.to_disk("./model/musicModel")



query = "Songs by Fall Out Boy like"

doc = nlp(query)

# Extract entities and their labels
entities = [(ent.text, ent.label_) for ent in doc.ents]

# Print the identified entities and their labels
for entity, label in entities:
    print(f"Entity: {entity}, Label: {label}")