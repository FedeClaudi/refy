# REFEREE
A papers recomendation tool

Referee compares papers in your library against a database of scientific papers to find new papers that you might be interested in.
While there's a few services out there that try to do the same, referee is unique in several ways:
* referee is completely open source, you can get the code and tweak it to improve the recomendation engine
* referee doesn't just use a single paper or a subset of (overly generic) keywords to find new papers, instead it compares *all* of your papers' abstracts against a database of papers metadata, producing much more relevant results

### disclaimer
The dataset used here is a subset of a [larger dataset of scientific papers](https://www.semanticscholar.org/paper/Construction-of-the-Literature-Graph-in-Semantic-Ammar-Groeneveld/649def34f8be52c8b66281af98ae884c09aef38b). The dataset if focused on neuroscience papers published in the latest 30 years. If you want to include older papers or are interested in another field, then follow the instructions to create your custom database. 

### (possible) future improvements
- [ ] use [scibert](https://github.com/allenai/scibert) instead of tf-idf for creating the embedding. This should also make it possible to embed the database's papers before use (unlike tf-idf which needs to run on the entire corpus every time).

### Overview
The core feature making referee unique among papers recomendation systems is that it analyzes **your entire library** of papers and matches it against a **vast database** of scientific papers to find new relevant papers. This is obviously an improvement compared e.g. to finding papers similar to *one paper you like*. 
In addition, referee doesn't just use things like "title", "authors", "keywords"... to find new matches, instead it finds similar papers using [*Term Frequency-Inverse Document Frequency*](https://en.wikipedia.org/wiki/Tf%E2%80%93idf) to asses the similarity across **papers abstracts**, thus using much more information about the papers' content. 

### Usage
First, you need to get data about your papers you want to use for the search. The best way is to export your library (or a subset of it) directly to a `.bib` file using your references menager of choice.

Then, you can use...


## Database
Referee uses a subset of the vast and eccelent corpus of scientific publications' metadata from [Semanthic Scholar](https://www.semanticscholar.org/paper/Construction-of-the-Literature-Graph-in-Semantic-Ammar-Groeneveld/649def34f8be52c8b66281af98ae884c09aef38b). 

### Downloading the dataset
One day the cleaned dataset will be put online in a way where it can easily (and automatically) be downloaded when using this software. 
Note however that the entire dataset is relatively large (~2GB) so it may take a while to download it. 

### Making your own database
The database used here is a medium size (800k papers) subset of the whole database, we've discarded papers that were published too long ago and that did not seem to be relevant for neuroscience. It's easy however to create your own version of the database to use for the searches. To do so:

1. Download the data from [Semanthic Scholar](http://s2-public-api-prod.us-west-2.elasticbeanstalk.com/corpus/download/)
2. Extract the compressed files and save the abstracts to a .txt file with `referee.database.upack_database`
3. Collate data from different files into a single one with: `referee.database.make_database`

The `unpack_database` step is the key one, that's when papers are discarded/included in the database. This steps uses parameters set in
`referee.settings` such that, e.g. `settings.fields_of_study` specifies which field of studies are relevant, papers from other fields will be discarded.
If you've cloned this repository and downloaded the compressed dataset, you can change the settings value and run the steps above to create your own database.