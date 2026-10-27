import logging
from Run import Github

def handler(event, context):
    logger = logging.getLogger()
    logger.info('Hello from main.py')

    '''Event Functionalities'''
    raw_data = event.get_raw_data() # raw event data
    logging.info('raw data: ' + str(raw_data))
    gh = Github()
    # gh.run_workflow()
    '''Context Functionalities'''
    # remaining_execution_time_ms = context.get_remaining_execution_time_ms()
    # max_execution_time_ms = context.get_max_execution_time_ms()
    # context.close_with_failure()
    context.close_with_success()
