from moodle_api.network import MoodleAPI
from moodle_api.pages import SummaryPage, FinishedAttemptPage, RunningAttemptPage
from moodle_api.parsers import TaskMetadata
from typing import Tuple
from utils import logger


def run_empty_attempt(api: MoodleAPI, cmid: str) -> None:
    response = api.get_summary_page(cmid=cmid)
    metadata = TaskMetadata(response.content)
    logger.info('No best attempt found. Starting new...')
    response = api.start_attempt(cmid, metadata.sesskey)
    attempt = RunningAttemptPage(response.content)
    logger.info('Finishing empty attempt...')
    answers = {}
    api.upload_answers(cmid, metadata.sesskey, attempt.id, attempt.prefix, answers)
    api.finish_attempt(cmid, metadata.sesskey, attempt.id)
    logger.info('Empty attempt is finished')
    return


def break_task(api: MoodleAPI, cmid: str) -> Tuple[dict, set]:
    response = api.get_summary_page(cmid=cmid)
    metadata = TaskMetadata(response.content)
    best_attempt = SummaryPage(response.content).best_attempt_id()
    if not best_attempt:
        run_empty_attempt(api, cmid)
        best_attempt = SummaryPage(response.content).best_attempt_id()
    logger.info(f'Found best attempt: {best_attempt}')
    best_attempt = SummaryPage(response.content).best_attempt_id()
    response = api.get_finished_attempt_page(cmid, best_attempt)
    answers = FinishedAttemptPage(response.content).parse_answers()
    logger.info(f'parsed answers for attempt {best_attempt}: {answers}')
    logger.info(f'Starting new attempt...')
    response = api.start_attempt(cmid, metadata.sesskey)
    attempt = RunningAttemptPage(response.content)
    missing_answers = attempt.all_questions.difference(set(answers.keys()))
    if missing_answers or not answers:
        logger.warning('missing answers: {}'.format(', '.join(missing_answers)))
        logger.warning('could parse: {}'.format(', '.join(answers)))
        logger.warning('Stopping breaking!')
        return answers, missing_answers
    logger.info(f'Uploading answers...')
    api.upload_answers(cmid, metadata.sesskey, attempt.id, attempt.prefix, answers)
    api.finish_attempt(cmid, metadata.sesskey, attempt.id)
    logger.info('Task is broken!')
    return answers, missing_answers
