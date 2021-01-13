from loguru import logger
from rich import print
import sys
from pathlib import Path
from myterial import orange

sys.path.append("./")
from refy.input import load_user_input
from refy.database import load_database
from refy.progress import suggest_progress
from refy.utils import to_table
from refy import doc2vec as d2v
from refy import download


def suggest_one(input_string, N=20, since=None, to=None, savepath=None):
    """
        Finds recomendations based on a single input string (with keywords,
        or a paper abstract or whatever) instead of an input .bib file

        Arguments:
            input_stirng: str. String to match against database
            N: int. Number of papers to suggest
            since: int or None. If an int is passed it must be a year,
                only papers more recent than the given year are kept for recomendation
            to: int or None. If an int is passed it must be a year,
                only papers older than that are kept for recomendation
            savepath: str, Path. Path pointing to a .csv file where the recomendations
                will be saved

        Returns:
            suggestions: pd.DataFrame of N recomended papers
    """
    download.check_files()

    # load database and abstracts
    database = load_database()

    # load model
    model = d2v.D2V()

    # find recomendations
    best_IDs = model.predict(input_string, N=N)

    # get selected papers
    suggestions = database.loc[database["id"].isin(best_IDs)].reset_index()
    suggestions["score"] = None

    # select papers based on date of publication
    if since:
        suggestions = suggestions.loc[suggestions.year >= int(since)]
    if to:
        suggestions = suggestions.loc[suggestions.year <= int(to)]

    # print
    print(
        to_table(
            suggestions,
            title=f'Suggestions for input string: [bold {orange}]"{input_string}"',
        )
    )

    # save to file
    if savepath:
        suggestions.to_csv(savepath)

    return suggestions


class suggest:
    suggestions_per_paper = 100  # for each paper find N suggestions

    def __init__(self, user_papers, N=20, since=None, to=None, savepath=None):
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
                savepath: str, Path. Path pointing to a .csv file where the recomendations
                    will be saved
        """
        download.check_files()

        self.since = since
        self.to = to
        if savepath:
            self.savepath = Path(savepath)
        else:
            self.savepath = savepath

        with suggest_progress as progress:
            self.progress = progress
            self.n_completed = -1
            self.task_id = self.progress.add_task(
                "Suggesting papers..", start=True, total=4, current_task="",
            )
            # load data
            self.load_data(user_papers)

            # load d2v model
            self._progress("Loading Doc2Vec model")
            self.d2v = d2v.D2V()

            # get suggestions
            self.get_suggestions(N=N)

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
                suggestions: pd.DataFrame with suggested papers ordred by score
        """
        # collate recomendations
        suggestions = self.database.loc[
            self.database.title.isin(points.keys())
        ].drop_duplicates(subset="title")

        # drop suggestions whose title is in the user papers
        titles = suggestions.title.apply(lambda x: x.lower().replace(" ", ""))
        user_titles = self.user_papers.title.apply(
            lambda x: x.lower().replace(" ", "")
        )
        suggestions = suggestions.loc[~titles.isin(user_titles)]

        # Get each paper's score
        max_score = self.suggestions_per_paper * self.n_user_papers
        suggestions["score"] = [
            points[title] / max_score for title in suggestions.title.values
        ]

        # sort recomendations based on score
        suggestions = suggestions.sort_values("score", ascending=False)

        # keep only papers published within a given years range
        if self.since:
            suggestions = suggestions.loc[suggestions.year >= int(self.since)]
        if self.to:
            suggestions = suggestions.loc[suggestions.year <= int(self.to)]

        suggestions = suggestions.reset_index(drop=True)

        return suggestions

    def get_suggestions(self, N=20):
        """
            Finds the papers from the database that are not in the user's
            library but are most similar to the users papers.
            For each user paper, get the N most similar papers, then get
            the papers that came up most frequently across all user papers.
            

            Arguments:
                N: int, number of best papers to keep

            Returns:
                suggestions: pd.DataFrame with suggested papers sorted by score
        """
        logger.debug(f"Getting suggestions for {self.n_user_papers} papers")

        # progress bar
        self._progress("Finding matches")
        select_task = self.progress.add_task(
            "Selecting best matches...",
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
        self.suggestions = self._collate_suggestions(points)[:N]
        print(to_table(self.suggestions))

        # save to file
        if self.savepath:
            self.suggestions.to_csv(self.savepath)

        return self.suggestions


if __name__ == "__main__":
    import refy

    refy.set_logging("DEBUG")
    suggest(refy.settings.example_path, N=100, since=2018)

    # suggest_one("locomotion control")
