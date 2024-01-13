import pandas as pd

print("Starting conversion (This will take a while!)")
csv_file_name = "song_lyrics.csv"
songs = pd.read_csv(csv_file_name)
songs = songs[['id', 'title', 'tag', 'artist', 'year', 'lyrics']]

non_misc = songs[songs['tag'] != 'misc']
non_misc.to_feather("songs_filtered.feather")

print("Finished conversion")
