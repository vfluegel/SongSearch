# SongSearch
Project for a Playlist Generator

## Preparation
_Note:_ PyLucene cannot be installed using pip. It needs to be [set up](https://lucene.apache.org/pylucene/install.html)
separately!

Due to the usage of PyLucene, the project needs to run with the system-wide Python
interpreter and its packages. The following additional packages need to be installed:
* Pandas
* Tkinter
* Tqdm
* Flair

The app uses a dataset based on Genius lyrics.
The CSV can be downloaded here:
https://www.kaggle.com/datasets/carlosgdcj/genius-song-lyrics-with-language-information/data

To use the data with the app, it needs to be converted:
1) Put the csv in the root directory of the project (or adjust path accordingly)
2) Execute csv_to_feather.py (requires Pandas)
3) A new file called songs_filtered.feather is generated

## Main App

The main app consists of three parts:
* Graphical user interface (-> songapp.py)
* PyLucene based search (-> lucene_searcher.py)
* Natural Language Query processing using Flair NER (-> query_processing.py)



To launch the app, execute songapp.py.  
First startup will take a while, as the index needs to be build and the model potentially downloaded. Subsequent startups will be faster.
