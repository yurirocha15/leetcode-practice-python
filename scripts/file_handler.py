import signal
from abc import ABC, abstractmethod
from typing import Dict, Type, TypeVar

from leetcode_client import LeetcodeClient
from question_db import QuestionData

T = TypeVar("T", bound="FileHandler")


class FileHandler(ABC):
    def __new__(cls: Type[T], data: QuestionData, language: str) -> T:
        subclasses: Dict[str, FileHandler] = {
            l: subclass for subclass in cls.__subclasses__() for l in subclass.languages
        }
        subclass = subclasses[language.lower()]
        instance = super(FileHandler, subclass).__new__(subclass)
        instance.set_question_data(data)
        return instance

    @abstractmethod
    def set_question_data(self, question_data: QuestionData):
        raise NotImplementedError

    @abstractmethod
    def generate_source(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def generete_tests(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate_submission_file(self):
        raise NotImplementedError


# helper function


def generate_files(
    args: Dict[int, QuestionData], qid: int, lc: LeetcodeClient, timestamp: float, language: str
):
    s = signal.signal(signal.SIGINT, signal.SIG_IGN)
    try:
        data, is_new = lc.get_question_data(
            qid,
            language,
            verbose=False,
        )
    except ValueError as e:
        print(e.args)
        signal.signal(signal.SIGINT, s)
        return

    if is_new and data.inputs and data.outputs:
        # generate
        data.creation_time = timestamp
        file_handler = FileHandler(data, language)
        data.file_path = file_handler.generate_source()
        data.test_file_path = file_handler.generete_tests()

        args[qid] = data
        print(f"""The question "{qid}|{data.title}" was imported""")
    signal.signal(signal.SIGINT, s)


# child classes (need to be imported in order to be instantiated)

from python_handler import PythonHandler
