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

This is what `refy` is for: **`refy` analyzes the abstracts of several papers of yours and matches them agaist published preprints**. By using many input papers at once `refy` has a lot more information at its disposal which (hopefully) means that it can better recommend relevant papers. By using the abstracts and not the paper titles, authors or keywords, `refy` focuses exclusively on the content of an article and has access to a wealth of data.

Refy downloads recently published preprints from BiorXiv and ArXiv, we thank BiorXiv and ArXiv for the API services they made freely available.

## Usage
### Installation
If you have an environment with `python >= 3.6`, you can install `refy` with:
```
pip install refy
```
### getting requests
```python
import refy

d = refy.Recomender(
 'library.bib',            # path to your .bib file
  n_days=30,               # fetch preprints from the last N days
  html_path="test.html",   # save results to a .html (Optional)
  N=10                     # number of recomended papers 
)
```
