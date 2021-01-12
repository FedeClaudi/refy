from loguru import logger
from rich import print
import sys

sys.path.append("./")
from referee.input import load_user_input
from referee.database import load_abstracts, load_database
from referee.progress import suggest_progress
from referee.utils import to_table
from referee import doc2vec as d2v
from referee.settings import example_path


class suggest:
    suggestions_per_paper = 100  # for each paper find N suggestions

    def __init__(self, user_papers, N=20):
        """
            Suggest new relevant papers based on the user's
            library.

            Arguments:
                user_papers: str, path. Path to a .bib file with user's papers info
                N: int. Number of papers to suggest
        """
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

            # get suggestions
            self.get_suggestions(N=N)

    @property
    def n_abstracts(self):
        return len(self.abstracts)

    @property
    def n_papers(self):
        return len(self.database)

    @property
    def n_user_papers(self):
        return len(self.user_papers)

    def paper_abstract(self, paper_id):
        """
            Returns a paper's abstract given the paper id string
        """
        try:
            self.abstracts[paper_id]
        except KeyError:
            raise ValueError(
                f"Could not find abstract for paper with ID: {paper_id}"
            )

    def _progress(self, task_name):
        """
            Update progress bar showing analysis status
        """
        self.n_completed += 1
        self.progress.update(
            self.task_id, current_task=task_name, completed=self.n_completed
        )

    def load_data(self, user_papers):
        """
            Load papers metadata for user papers
            and database papers

            Arguments:
                user_papers: str, path. Path to a .bib file with user's papers info
        """
        # load database and abstracts
        self._progress("Loading database abstracts",)
        self.abstracts = load_abstracts()

        self._progress("Loading database papers")
        self.database = load_database()

        if self.n_papers != self.n_abstracts:
            raise ValueError(
                "Error while loading data. Expected same number of papers and abstracts."
                f"Instead {self.n_papers} papers and {self.n_abstracts} abstracts were found"
            )

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
                f"with abstract:{self.paper_abstract(user_paper_title)}"
            )

        return {
            t: self.suggestions_per_paper - n
            for n, t in enumerate(selected.title.values)
        }

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
        self._progress("Finding matches")
        select_task = self.progress.add_task(
            "Selecting best matches...",
            start=True,
            total=self.n_user_papers,
            current_task="analyzing...",
        )

        # find best matches for each paper
        counts = {}
        for n, (idx, user_paper) in enumerate(self.user_papers.iterrows()):
            # keep track of recomendations across all user papers
            paper_suggestions = self.suggest_for_paper(
                user_paper.title, user_paper.abstract
            )

            for suggested, points in paper_suggestions.items():
                if suggested in counts.keys():
                    counts[suggested] += points
                else:
                    counts[suggested] = points

            self.progress.update(select_task, completed=n)
        self.progress.remove_task(select_task)
        self.progress.remove_task(self.task_id)

        # collate recomendations
        suggestions = self.database.loc[
            self.database.title.isin(counts.keys())
        ].drop_duplicates(subset="title")

        # Get each paper's score
        max_score = self.suggestions_per_paper * self.n_user_papers
        suggestions["score"] = [
            counts[title] / max_score for title in suggestions.title.values
        ]

        # sort recomendations based on score
        suggestions = suggestions.sort_values(
            "score", ascending=False
        ).reset_index()

        print(to_table(suggestions[:N]))


if __name__ == "__main__":
    suggest(example_path, N=100)
