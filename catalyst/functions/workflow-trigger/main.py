import logging
from Run import Github

def handler(event, context):
    logger = logging.getLogger()
    logger.info('Hello from main.py')

    '''Event Functionalities'''
    raw_data = event.get_raw_data() # raw event data
    file_key = raw_data["events"][0]["data"]["object_details"][0]["key"]
    logger.info(file_key)
    gh = Github()
    gh.run_workflow(file_key)
    '''Context Functionalities'''
    # remaining_execution_time_ms = context.get_remaining_execution_time_ms()
    # max_execution_time_ms = context.get_max_execution_time_ms()
    # context.close_with_failure()
    context.close_with_success()
