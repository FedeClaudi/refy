# refy
A papers recomendation tool

refy compares papers in your library against a database of scientific papers to find new papers that you might be interested in.
While there's a few services out there that try to do the same, refy is unique in several ways:
* refy is completely open source, you can get the code and tweak it to improve the recomendation engine
* refy doesn't just use a single paper or a subset of (overly generic) keywords to find new papers, instead it compares *all* of your papers' abstracts against a database of papers metadata, producing much more relevant results

### disclaimer
The dataset used here is a subset of a [larger dataset of scientific papers](https://www.semanticscholar.org/paper/Construction-of-the-Literature-Graph-in-Semantic-Ammar-Groeneveld/649def34f8be52c8b66281af98ae884c09aef38b). The dataset if focused on neuroscience papers published in the latest 30 years. If you want to include older papers or are interested in another field, then follow the instructions to create your custom database. 

### (possible) future improvements
- [ ] use [scibert](https://github.com/allenai/scibert) instead of tf-idf for creating the embedding. This should also make it possible to embed the database's papers before use (unlike tf-idf which needs to run on the entire corpus every time).

### Overview
The core feature making refy unique among papers recomendation systems is that it analyzes **your entire library** of papers and matches it against a **vast database** of scientific papers to find new relevant papers. This is obviously an improvement compared e.g. to finding papers similar to *one paper you like*. 
In addition, refy doesn't just use things like "title", "authors", "keywords"... to find new matches, instead it finds similar papers using [*Term Frequency-Inverse Document Frequency*](https://en.wikipedia.org/wiki/Tf%E2%80%93idf) to asses the similarity across **papers abstracts**, thus using much more information about the papers' content. 

### Usage
First, you need to get data about your papers you want to use for the search. The best way is to export your library (or a subset of it) directly to a `.bib` file using your references menager of choice.

Then, you can use...


## Making your own database
refy uses a subset of the vast and eccelent corpus of scientific publications' metadata from [Semanthic Scholar](https://www.semanticscholar.org/paper/Construction-of-the-Literature-Graph-in-Semantic-Ammar-Groeneveld/649def34f8be52c8b66281af98ae884c09aef38b). 
The dataset used by refy is focused on neuroscience papers written in english and published in the last 30 years. If you wish to include a different set of papers in your database, you can make your custom database and use it with refy by executing the following steps.

### 1. Download whole corpus
You'll first need to download the whole corpus from Semantic Scholar. You can find the data and download instructions [here](http://s2-public-api-prod.us-west-2.elasticbeanstalk.com/corpus/download/). Once the data are downloaded, save them in a folder where you want to base your dataset-creation process

### 2. Uncompressing data
The downloaded corpus is compressed. To uncompress the files use `refy.database_preprocessing.upack_database` pasing to it the path to the folder where you've downloaded the data.

### 3. Specifying your parameters
The selection of a subset of papers from the corpus is based on a set of parameters (e.g. year of publication) matched against criteria specified (and described) in `refy.settings`. Edit the criteria to adapt the dataset selection to your needs

### 4. Creating the dataset
Simply run `refy.database_preprocessing.make_database`

### 5. Training doc2vec model
Papers semanthic similarity is estimated using a doc2vec model trained on the entire dataset.
After modifying the dataset to your needs, you'll have to re-train the model by running `refy.doc2vec.train_doc2vec_model`

### summary:
An example code for creating your dataset (after having downloaded the corpus and edited the settings)
``` python

from refy.database_preprocessing import upack_database, make_database
from refy.doc2vec import train_doc2vec_model
from pathlib import Path

folder = Path('path to your data')

# unpack and create
unpack_database(folder)
make_database(folder)

# train new d2v model
train_doc2vec_model()

```

