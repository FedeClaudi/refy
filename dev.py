# from referee import suggest
from referee.settings import base_dir
from referee.utils import from_txt
from rich.progress import track
import json

data = {}

abstracts_dir = base_dir / "abstracts"
for fl in track(list(abstracts_dir.glob("*.txt"))):
    name = fl.name.split(".")[0]
    data[name] = from_txt(fl)

print("writing")
with open(abstracts_dir.parent / ("abstrcts" + ".json"), "w") as out:
    json.dump(data, out)

# bib_file = (
#     "/Users/federicoclaudi/Downloads/Paperpile - Jan 05 BibTeX Export.bib"
# )

# suggest(bib_file)


# if __name__ == "__main__":
#     fld = r"M:\PAPERS_DBASE"
#     # upack_database(fld)

#     make_database(fld)
