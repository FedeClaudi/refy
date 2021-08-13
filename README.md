# refy
A scientific papers recommendation tool.

**docs:** https://federicoclaudi.gitbook.io/refy/

## Usage
### Installation
If you have an environment with `python >= 3.6`, you can install `refy` with:
```
pip install refy
```
### getting suggested papers
```python
import refy

d = refy.Recomender(
 'library.bib',            # path to your .bib file
  n_days=30,               # fetch preprints from the last N days
  html_path="test.html",   # save results to a .html (Optional)
  N=10                     # number of recomended papers 
)
```
