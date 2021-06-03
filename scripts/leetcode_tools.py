import os
import platform
import signal
import time
from multiprocessing import Manager, Process
from multiprocessing.managers import SyncManager
from pathlib import Path
from re import T
from typing import Any, Dict, final

import clize
from file_handler import FileHandler, generate_files
from leetcode_client import LeetcodeClient
from my_utils import mgr_init
from question_db import QuestionData, QuestionDB
from readme_handler import ReadmeHandler

# TODO: change this to a config file
_LANGUAGE = "python3"


def get_question(id: int):
    """Generates all the files for a question

    Args:
        id (int): the question id
    """
    lc = LeetcodeClient()
    qdb = QuestionDB()
    qdb.load()

    if qdb.check_if_exists(id):
        print("Question already imported")
        return

    if not qdb.check_if_slug_is_known(id):
        qdb.set_id_title_map(lc.get_id_title_map())
        qdb.save()

    # get question data
    args: Dict[int, QuestionData] = {}
    generate_files(args, id, qdb.get_title_from_id(id), lc, time.time(), _LANGUAGE)

    if id in args:
        # store data
        qdb.add_question(args[id])
        qdb.save()

        # update readme
        rh = ReadmeHandler()
        rh.build_readme(qdb.get_sorted_list(sort_by="creation_time"))


def submit_question(id: int):
    # submissions
    qdb = QuestionDB()
    qdb.load()
    problems = qdb.get_data()
    # create submit file
    if qdb.check_if_exists(id):
        file_handler = FileHandler(qdb.get_question(id), _LANGUAGE)
        code = file_handler.generate_submission_file()

        lc = LeetcodeClient()
        try:
            lc.submit_question(code, qdb.get_question(id).internal_id, _LANGUAGE)
        except Exception as e:
            print(e.args)
    else:
        print(f"Could not find the question with id {id}")


def get_all_submissions():
    """Get all solutions and generate their files"""
    lc = LeetcodeClient()
    qdb = QuestionDB()
    qdb.load()
    has_next: bool = True
    last_key: str = ""
    offset: int = 0
    imported_cnt = 0

    try:
        while has_next:
            jobs = []
            manager = SyncManager()
            manager.start(mgr_init)
            ret_dict = manager.dict()
            submissions = lc.get_submission_list(last_key, offset)
            for submission in submissions["submissions_dump"]:
                qid: int = -1
                if qdb.check_if_id_is_known(submission["title_slug"]):
                    qid = qdb.get_id_from_title(submission["title_slug"])
                else:
                    qdb.set_id_title_map(lc.get_id_title_map())
                    qdb.save()
                    qid = qdb.get_id_from_title(submission["title_slug"])
                if (
                    submission["status_display"] == "Accepted"
                    and submission["lang"] == _LANGUAGE
                    and not qdb.check_if_exists(qid)
                ):
                    if not qdb.check_if_exists(qid):
                        # pre-store the question
                        data = QuestionData(id=qid)
                        qdb.add_question(data)
                        p = Process(
                            target=generate_files,
                            args=(
                                ret_dict,
                                qid,
                                submission["title_slug"],
                                lc,
                                submission["timestamp"],
                                _LANGUAGE,
                                submission["code"],
                            ),
                        )
                        jobs.append(p)
                        p.start()

            for p in jobs:
                p.join()

            for data in ret_dict.values():
                qdb.add_question(data)
                imported_cnt += 1

            has_next = submissions["has_next"]
            last_key = submissions["last_key"]
            offset += 20
            qdb.save()
    except KeyboardInterrupt:
        print("Stopping the process...")
        for p in jobs:
            p.join()
        for data in ret_dict.values():
            qdb.add_question(data)
            imported_cnt += 1
    except Exception as e:
        print(e.args)
    finally:
        manager.shutdown()

    qdb.save()
    # update readme
    rh = ReadmeHandler()
    rh.build_readme(qdb.get_sorted_list(sort_by="creation_time"))

    print(f"In total, {imported_cnt} questions were imported!")


def remove_question(id: int):
    qdb = QuestionDB()
    qdb.load()
    if qdb.check_if_exists(id):
        data = qdb.get_data()[id]
        try:
            os.remove(data.file_path)
            os.remove(data.test_file_path)
        except FileNotFoundError as e:
            print(e.args)
        qdb.delete_question(id)
        qdb.save()
        # update readme
        rh = ReadmeHandler()
        rh.build_readme(qdb.get_sorted_list(sort_by="creation_time"))
    else:
        print(f"The question {id} could not be found!")


def get_all_questions():
    lc = LeetcodeClient()
    lc.get_all_questions_data(lc.get_cookies()[0])


if __name__ == "__main__":
    clize.run(
        get_question,
        submit_question,
        get_all_submissions,
        remove_question,
        get_all_questions,
    )
