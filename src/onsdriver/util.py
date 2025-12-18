'''
This module provides useful functions when testing with obs-studio.
'''

import time

def retry(timeout, each_wait=0.1, error_msg=None):
    '''Retry until meeting a condition
    Use this function with `while` statement like below.
    while retry(timeout=10):
        good = your_task()
        if good:
            break
    :param timeout:    Set the timeout in second
    :param each_wait:  Sleep time for each
    '''
    yield None

    count = int(timeout // each_wait + 0.5)
    while count > 0:
        time.sleep(each_wait)
        yield None
        count -= 1

    raise TimeoutError(error_msg)
