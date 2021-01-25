# refy
A scientific papers recommendation tool.

## Overview
`refy` leverages Natural Langual Processing (NLP) machine learning tools to find new papers that might be relevant given the ones that you've read already. 

There's a few software tools out there that facilitate the exploration of scientific literature, including:
* [meta.org](https://www.meta.org/) which allows users to set up feeds that identify newly published papers that seem relevant given a set of *keywords*
* [inciteful](https://inciteful.xyz/) and [scite.ai](https://scite.ai/) let you explore the network of citations around a given paper of interest
* [connected papers](https://www.connectedpapers.com/) let's you visualize a graph representation of papers related to a given paper of interest

Most currently available software is limited in two key ways:
1. Tools like [meta.org](https://www.meta.org/) rely on keywords, but keywords (e.g. computational neuroscience, Parkinson's Disease) are often overly general. As a result of that you have to sift through a lot irrelevant literature before you find something interesting
2. Other tools like [connected papers](https://www.connectedpapers.com/) only work with one input paper at the time: you give it the title of a paper you've read and they give you suggestions. This is limiting: any software that can analyse **all papers you've read** can use a lot more information to find new papers that match more closely your interests.

This is what `refy` is for: **`refy` analyzes the abstracts of several papers of yours and matches them agaist a database of almost ONE MILLION paper abstracts**. By using many input papers at once `refy` has a lot more information at its disposal which (hopefully) means that it can better recommend relevant papers. More details about the database used by `refy` can be found at the bottom of this document. 

>**Disclaimer:** The database used by `refy` is focused on neuroscience papers and preprints published in the last 30 years. If you are interested in older papers or work in a different field, please read the instructions below about how to adjust the database to your needs.

## Usage
### Installation
If you have an environment with `python >= 3.6`, you can install `refy` with:
```
pip install refy
```

You can check if everything went okay with:
```
refy example
```
which should print something like:

<p align="center">
<img src="imgs/example.png" width=800px style='margin:auto'></img>
</p>


### Usage
`refy` provides a Command Line Interface (CLI) to expose it's functionality directly in your terminal:
<p align="center">
<img src="imgs/helptxt.png" width=800px style='margin:auto'></img>
</p>

>**Note:** the first time you use `refy` it will have to download several files (which you can see [here](https://gin.g-node.org/FedeClaudi/refy/src/master/)) with data it needs to work. This should only take a few minuts and it will take up about 3GB of your hard disk space.

You can use `refy` in three modes:
1. In `query` mode you can find papers relevant for a given input string (e.g. `locomotion mouse brainstem`)
2. In `suggest` mode you give `refy` a `.bib` [bibtext file](https://en.wikipedia.org/wiki/BibTeX) with metadata about as many publications as you want. `refy` will use this information to find papers relevant across all of your input papers.
3. `daily` suggests relevant papers from those released on biorxiv.org in the last 24 hours (see below)

For **query mode** you will use the command `refy query STRING`, for `suggest` you'd use `refy suggest PATH`.

 In all cases you can use optional arguments:
```shell
    -N INTEGER            number of recommendations to show  [default: 10]
    -since INTEGER        Only keep papers published after SINCE
    -to INTEGER           Only keep papers published before TO
    -save-path, --s TEXT  Save suggestions to file
    -debug, --d           set debug mode ON/OFF  [default: False]
```

For example:
```shell
refy query "locomotion control brainstem" --N 100 --since 2015 --to 2018 --s refs.csv
```
Will show 100 suggested papers published between 2015 and 2018 related to locomotrion control and will save the results to `refs.csv`.


>**Note:** `suggest` mode is much more powerful and hence it's the recommended way for finding new literature, however `query` allows you to quickly look up new papers without having to createa a `.bib` field. 
>**Note:** in `suggest` mode, the content of your `.bib` file **must** include papers abstracts. **Only papers with abstracts** will be used for the analysis. Your `.bib` file entries should look like this:
```
@ARTICLE{Claudi2020-tb,
  title    = "Brainrender. A python based software for visualisation of
              neuroanatomical and morphological data",
  author   = "Claudi, Federico and Tyson, Adam L and Branco, Tiago",
  abstract = "Abstract Here we present brainrender, an open source python
              package for rendering three-dimensional neuroanatomical data
              aligned to the Allen Mouse Atlas. Brainrender can be used to
              explore, visualise and compare data from publicly available
              datasets (e.g. from the Mouse Light project from Janelia) as well
              as data generated within individual laboratories. Brainrender
              facilitates the exploration of neuroanatomical data with
              three-dimensional renderings, aiding the design and
              interpretation of experiments and the dissemination of anatomical
              findings. Additionally, brainrender can also be used to generate
              high-quality, publication-ready, figures for scientific
              publications.",
  journal  = "Cold Spring Harbor Laboratory",
  pages    = "2020.02.23.961748",
  month    =  feb,
  year     =  2020,
  language = "en",
  doi      = "10.1101/2020.02.23.961748"
}
``` 

> **hint:** if you use reference managers like zotero or paperpile you can easily export bibtext data about your papers

`refy` has two kind of outputs:
1. It will print to terminal a list of N recommended paper, sorted by their recommendation score. It will also show keywords that appear in your input papers and the authors that came up most frequently in your recommendations. See the figure at the top of this document for reference.
2. Optionally, `refy` can save the list of recommended paper to ` .csv` file so that you may explore these at your leasure.

> **hint: ** the DOIs on the right of the report are working links (if you terminal supports links)!

### Daily
Hard to keep up with all the preprints that come out all the time? Fear not, `refy`'s `daily` function is here to help. In your terminal, call `refy daily mybib.bib` and `refy` will recomend papers from those that came out of biorxiv in the last 24 hours. You can use the `-N` argument to specify how many suggestions you'd like to see. 

If you are using Mac or Linux, `refy` has a (still experimental) feature which enables you to run `refy daily` everyday automatically. To do so, call `refy setup-daily` which will create a [crontab](https://en.wikipedia.org/wiki/Cron) job which runs `refy daily` everyday at 10. If you'd like to change the time at which it runs you can edit the crontab job with `crontab -e`.

For `refy setup-daily` to work, you will need to provide your user name, a path to a python executable (which has access to a refy installation), a path to your `.bib` file and then with the `-o` option you can specify a path to a `.html` file. The output of running `refy daily` will be saved as a `.html` file which you can open in your browser. So for instance, this is how I called `refy setup-daily`:
```
sudo refy setup-daily "federico claudi" "/Users/federicoclaudi/miniconda3/envs/ref/bin/python" "/Users/federicoclaudi/Documents/Github/referee/test.bib" -N 20 -o /Users/federicoclaudi/Desktop/refy.html
```

Notice the `sudo` before the command as `crontab` needs to have admin privileges.

### Scripting
You can of course access all functionality through normal python scripts. For instance:
```python
from refy import suggest

rec = suggest('my_library.bib')
print(rec.suggestions)
```

## Under the hood
This section explains how `refy` works. If you just want to use `refy` and don't care about what happens under the hood then feel free to skip this. 

`refy` uses NLP algorithms to estimate semantic similarity across papers based on the content of their abstracts. In particular, it uses [`Doc2Vec`](https://medium.com/wisio/a-gentle-introduction-to-doc2vec-db3e8c0cce5e) which is an adaptation of `Word2Vec`, a model that embeddings of words in which semantically similar words are closer in the embedding space than semantically dissimilar words are. `Dov2Vec` expands `Word2Vec` to learn vector embedding of entire documents.

The `Doc2Vec` model used here is train on the entire corpus of almost one million papers. When it comes finding recommendations for your papers, `refy` uses `Doc2Vec` to create a vector representation of your paper and find the N closest vectors which, hopefully, are papers that are similar to yours. 

This operation is repeated for each paper in your `.bib` file and then recommendations are pooled and scored: the papers that scored highest for the most number of input papers will be the most strongly recommended ones. 

## Database
`refy` uses a curated database of about one million papers metadata to recommend literature for you. TJe data come from two sources:
* [semantic scholar's Open Corpus](https://www.semanticscholar.org/paper/Construction-of-the-Literature-Graph-in-Semantic-Ammar-Groeneveld/649def34f8be52c8b66281af98ae884c09aef38b) 
* [biorxiv](https://api.biorxiv.org/)

Data from these two vasts databases (several million publications) are filtered to selectively keep neuoroscience and ML papers written in english and published in the last 30 years. This selection is necessary to keep the compute and memory requirements within reasonable bounds. 

If **you wish to create your custom database**, these are the steps you'll need to follow:
1. download the compressed data from [semantic scholar's Open Corpus](http://s2-public-api-prod.us-west-2.elasticbeanstalk.com/corpus/download) and save them in a folder. Note the entire database is >100GB in size even while compressed so it might take a while
2. clone this repository with `git clone https://github.com/FedeClaudi/refy.git`
3. in the shell `cd refy`
4. within the cloned repository edit `refy/settings.py`. In it there are a few settings that apply to the creation of database (e.g. select papers based on the year of publication). Set these settings to values that match your need
5. Install the edited version of `refy` with `pip install . -U`
6. Create the edited database with `refy update_database FOLDER` where `FOLDER` is the path to where you saved the data downloaded from semantic scholar

Once the database update has finished (should take <5 hours), you can re-train the `Doc2Vec` model to fit it to your database with `refy train` (use `refy train --help` to see the options available). This step will like require ~12 hours but the duration depend on the specs of your machine and the size of the database as you've created it. 

