from loguru import logger
import sys

from pyinspect.panels import Report
from myterial import orange, salmon, orange_dark

sys.path.append("./")
from refy.input import load_user_input
from refy.database import load_database
from refy.progress import suggest_progress
from refy import doc2vec as d2v
from refy.suggestions import Suggestions
from refy.authors import Authors
from refy._query import SimpleQuery


class suggest(SimpleQuery):
    suggestions_per_paper = 100  # for each paper find N suggestions

    def __init__(
        self,
        user_papers,
        N=20,
        since=None,
        to=None,
        csv_path=None,
        html_path=None,
    ):
        """
            Suggest new relevant papers based on the user's
            library.

            Arguments:
                user_papers: str, path. Path to a .bib file with user's papers info
                N: int. Number of papers to suggest
                since: int or None. If an int is passed it must be a year,
                    only papers more recent than the given year are kept for recomendation
                to: int or None. If an int is passed it must be a year,
                    only papers older than that are kept for recomendation
                csv_path: str, Path. Path pointing to a .csv file where the recomendations
                    will be saved
                html_path: str, Path. Path to a .html file 
                    where to save the output
        """
        SimpleQuery.__init__(self, csv_path=csv_path, html_path=html_path)

        self.since = since
        self.to = to

        with suggest_progress as progress:
            self.progress = progress
            self.n_completed = -1
            self.task_id = self.progress.add_task(
                "Suggesting papers..", start=True, total=5, current_task="",
            )
            # load data
            self.load_data(user_papers)

            # load d2v model
            self._progress("Loading Doc2Vec model")
            self.d2v = d2v.D2V()

            # get keywords
            self._progress("Extracting keywords from data")
            self.get_keywords(self.user_papers)

            # get suggestions
            self.get_suggestions(N=N)
        self.print()

        # save to .csv and .HTML file
        self.to_csv()
        self.to_html()

    @property
    def n_papers(self):
        return len(self.database)

    @property
    def n_user_papers(self):
        return len(self.user_papers)

    def _progress(self, task_name):
        """
            Update progress bar
        """
        self.n_completed += 1
        self.progress.update(
            self.task_id, current_task=task_name, completed=self.n_completed
        )

    def load_data(self, user_papers):
        """
            Load papers metadata for user papers and database papers

            Arguments:
                user_papers: str, path. Path to a .bib file with user's papers info
        """
        # load database
        self._progress("Loading database papers")
        self.database = load_database()

        # load user data
        self._progress("Loading user papers",)
        self.user_papers = load_user_input(user_papers)

    def suggest_for_paper(self, user_paper_title, user_paper_abstract):
        """
            Finds the best matches for a single paper

            Arguments:
                user_paper_title: str. Title of input user paper
                user_paper_abstract: str. Abstract of input user paper

            Returns:
                suggestions: dict. Dictionary of title:value where value 
                    is self.suggestions_per_paper for the best match paper and 
                    1 for the lowest match
        """
        # find best match with d2v
        best_IDs = self.d2v.predict(
            user_paper_abstract, N=self.suggestions_per_paper
        )

        # get selected papers
        selected = self.database.loc[self.database["id"].isin(best_IDs)]

        if selected.empty:
            logger.debug(
                f'Could not find any suggested papers for paper: "{user_paper_title}" '
            )

        return {
            t: self.suggestions_per_paper - n
            for n, t in enumerate(selected.title.values)
        }

    def _collate_suggestions(self, points):
        """
            Given a dictionart of points for each suggested paper,
            this function returns a dataframe with papers ordered 
            by their score

            Arguments:
                points: dict of title:point entries for each recomended paper

            Returns
                suggestions: Suggestions with suggested papers ordred by score
        """
        # collate recomendations
        suggestions = Suggestions(
            self.database.loc[self.database.title.isin(points.keys())]
        )

        # drop suggestions whose title is in the user papers
        suggestions.remove_overlap(self.user_papers)

        # Get each paper's score
        max_score = self.suggestions_per_paper * self.n_user_papers
        score = [points[title] / max_score for title in suggestions.titles]
        suggestions.set_score(score)

        # keep only papers published within a given years range
        suggestions.filter(to=self.to, since=self.since)

        return suggestions

    def get_suggestions(self, N=20):
        """
            Finds the papers from the database that are not in the user's
            library but are most similar to the users papers.
            For each user paper, get the N most similar papers, then get
            the papers that came up most frequently across all user papers.
            

            Arguments:
                N: int, number of best papers to keep

        """
        logger.debug(f"Getting suggestions for {self.n_user_papers} papers")

        # progress bar
        self._progress("Looking for good papers")
        select_task = self.progress.add_task(
            "Selecting the very best...",
            start=True,
            total=self.n_user_papers,
            current_task="analyzing...",
        )

        # find best matches for each paper
        points = {}
        for n, (idx, user_paper) in enumerate(self.user_papers.iterrows()):
            # keep track of recomendations across all user papers
            paper_suggestions = self.suggest_for_paper(
                user_paper.title, user_paper.abstract
            )

            for suggested, pts in paper_suggestions.items():
                if suggested in points.keys():
                    points[suggested] += pts
                else:
                    points[suggested] = pts

            self.progress.update(select_task, completed=n)
        self.progress.remove_task(select_task)
        self.progress.remove_task(self.task_id)

        # collate and print suggestions
        self.suggestions = self._collate_suggestions(points)
        self.suggestions.get_authors()

        self.suggestions.truncate(N)

    def _make_summary(self, *args, **kwargs):
        """
            Creates a summary with suggestions, authors
            and keywords metadata etc. 

            Arguments:
                *args, **kwargs: not used, for compatibility with
                    SimpleQuery.print's compatibility

            Returns:
                summary: Summary with all information about the results
        """
        # create a list of most recomended authors
        authors = Authors(self.suggestions.authors)

        # get console with highlighter
        highlighter = self.keywords.get_highlighter()

        # create summary
        summary = Report(dim=orange)
        summary.width = 160

        # keywords
        summary.add(f"[bold {salmon}]:mag:  [u]keywords\n")
        summary.add(self.keywords.to_table(), "rich")
        summary.spacer()
        summary.line(orange_dark)
        summary.spacer()

        # suggestions
        summary.add(f"[bold {salmon}]:memo:  [u]recomended paper\n")
        summary.add(self.suggestions.to_table(highlighter=highlighter), "rich")
        summary.spacer()
        summary.line(orange_dark)
        summary.spacer()

        # authors
        summary.add(f"[bold {salmon}]:lab_coat:  [u]top authors\n")
        summary.add(authors.to_table(), "rich")
        summary.spacer()

        return summary


if __name__ == "__main__":
    import refy

    refy.settings.TEST_MODE = False

    refy.set_logging("DEBUG")

    suggest(refy.settings.example_path, N=25, since=2018).print()
