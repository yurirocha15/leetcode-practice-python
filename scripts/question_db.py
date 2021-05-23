import operator
import os
import pickle
import time
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class QuestionData:
    title: str = ""
    url: str = ""
    id: int = 0
    creation_time: float = 0.0
    difficulty: str = ""
    function_name: str = ""
    file_path: str = ""
    test_file_path = ""
    raw_code: str = ""
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    categories: List[Dict[str, str]] = field(default_factory=list)


class QuestionDB:
    """Handles the question data"""

    def __init__(self):
        self.db_file = "bin/question_data.pkl"
        self.question_data_dict: Dict[int, QuestionData] = {}

    def load(self):
        """Load the question data from disk"""
        if os.path.isfile(self.db_file):
            with open(self.db_file, "rb") as f:
                self.question_data_dict = pickle.load(f)

    def save(self):
        """Save the question data to disk"""
        with open(self.db_file, "wb") as f:
            pickle.dump(self.question_data_dict, f)

    def get_data(self) -> Dict[int, QuestionData]:
        """Returns the question data

        Returns:
            Dict[int, QuestionData]: A dictionary whose the question id is its key.
        """
        return self.question_data_dict

    def add_question(self, qd: QuestionData):
        """Add a question to the dictionary

        Args:
            qd (QuestionData): The question data
        """
        self.question_data_dict[qd.id] = qd

    def delete_question(self, id: int):
        """Removes a question from the dictionary

        Args:
            id (int): the question id
        """
        if id in self.question_data_dict:
            self.question_data_dict.pop(id)

    def get_sorted_list(self, sort_by: str) -> List[QuestionData]:
        """Returns a sorted list with all the questions

        Args:
            sort_by (str): the attribute used to sort the list.
            Can be any QuestionData attribute.

        Returns:
            List[QuestionData]: [description]
        """
        return sorted(self.question_data_dict.values(), key=operator.attrgetter(sort_by))

    def check_if_exists(self, id: int) -> bool:
        """Checks if a question exists in the database

        Args:
            id (int): the question id

        Returns:
            bool: true if the question exists in the database
        """
        return id in self.question_data_dict
